# change NODETAG to switch between nodes
# on both researcher and node sides
export NODETAG=TODO # adni, calgary, pad, ppmi, qpn, mega
export NODE=node-${NODETAG}
cd ${FEDBIOMED_DIR}/envs/vpn/docker

# server side
docker compose exec vpnserver bash -ci "python ./vpn/bin/configure_peer.py genconf node ${NODETAG}"
docker compose exec vpnserver cat /config/config_peers/node/${NODETAG}/config.env
# node side
code /tmp/config-${NODETAG}.env
# change IP address to public IP 206.12.94.146
cp /tmp/config-${NODETAG}.env ./${NODE}/run_mounts/config/config.env

# start the node
docker compose up -d ${NODE}
# change the node name in its config.ini
code ./${NODE}/run_mounts/fbm-node/etc/config.ini
# restart the node to apply changes
docker compose down ${NODE}
docker compose up -d ${NODE}

# get the node's publickey
docker compose exec ${NODE} wg show wg0 public-key | tr -d '\r' >/tmp/publickey-nodeside-${NODETAG}
cat /tmp/publickey-nodeside-${NODETAG}

# copy to server side
code /tmp/publickey-serverside-${NODETAG}
docker compose exec vpnserver bash -ci "python ./vpn/bin/configure_peer.py add node ${NODETAG} $(cat /tmp/publickey-serverside-${NODETAG})"

# test the node
${FEDBIOMED_DIR}/scripts/fedbiomed_vpn status ${NODE}

# add the dataset to the node
docker compose exec -u $(id -u) ${NODE} bash
fedbiomed node dataset add --file /_dataset_configs/${NODETAG}.json

# add training plans on server side
docker compose exec -u $(id -u) researcher bash
/fl-pd/scripts/register_training_plan.py / --target 'fl:cognitive_decline_status'
/fl-pd/scripts/register_training_plan.py / --target 'nb:Age'

# approve on node side
docker compose exec -u $(id -u) ${NODE} bash
fedbiomed node training-plan approve

# # launch all nodes
# for DATASET in "adni" "calgary" "mega" "pad" "ppmi" "qpn"; do docker compose up -d node-${DATASET}; done

# run
docker compose exec -u $(id -u) researcher bash
/fl-pd/scripts/run_fedbiomed_custom_dataset.py --null 10 /fl-pd/data /fl-pd/results / /fl-pd/data/latest/_stats --random-state 3791 --target 'fl:cognitive_decline_status' &> /fl-pd/logs/`date +%Y%m%d_%H%M`.log &
/fl-pd/scripts/run_fedbiomed_custom_dataset.py --null 10 /fl-pd/data /fl-pd/results / /fl-pd/data/latest/_stats --random-state 3791 --target 'nb:Age' &> /fl-pd/logs/`date +%Y%m%d_%H%M`.log &

