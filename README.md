# Shadow Dashboard

## Local Host

> WARNING: This type of deployment is still a work in progress. 
> WARNING: This type of deployment is very slow!

This is intended for use on a single development machine.

Use the `docker-compose.yml.singleHost` configuration file. It must be renamed to be detected by docker.
```bash
$ cp docker-compose.yml.singleHost docker-compose.yml
```

### Steps to update the deployment

```bash
$ docker-compose up -d
```

The dashboard will be available on `localhost:8080`.

## Cluster

###  Setting up the environment 

This is intended for use on a cluster of computers connected through docker swarm that have access to a common NFS file storage system.

Use the `docker-compose.yml.swarm` configuration file. It must be renamed to be detected by docker.
```bash
$ cp docker-compose.yml.swarm docker-compose.yml
```

The docker configuration provided requires access to a docker registry, NFS storage with read and write access and a docker swarm cluster. The user must have read and write access to the docker registry and be able to deploy docker compose configurations to the docker swarm. The variables for these can be found in the `.env` file in the root of the project. Additionally, DASHBOARD_HOSTNAME in `.env` should be set to the hostname of the machine where the dashboard will be hosted on.

> Note: Internet access is required to build the docker images

> If running from inside GMU CARE: No changes are needed if you are running from `sr4s5.mesa.gmu.edu`.

### Steps to update the deployment

Run `make all` from the root of the repository. This machine must have access to a docker registry. This will build the images, push them to the private docker registry and then update the docker swarm.

The dashboard will be available on `${DASHBOARD_HOSTNAME}:8080`.

### Manually

- First update the docker image `shadow-dashboard:amd64` by building the docker image from the `Dockerfile` in the `shadow-dashboard` directory. Run `docker build . -t ${DOCKER_REGISTRY}/shadow-dashboard:amd64 --platform linux/amd64` for this
- Push the updated docker image to the registry by running `docker push ${DOCKER_REGISTRY}/shadow-dashboard:amd64`
- Log in to a machine that has access to the docker registry and cluster. Run `docker service update shadow-dashboard_dashboard --with-registry-auth --image ${DOCKER_REGISTRY}/shadow-dashboard:amd64` This will update the deployment with the new image

## Data Format 

The data uploaded to the dashboard for processing should be a `.zip` file with the following structure:

```
data.zip/
    1.pcap
    2.pcap
    ...
    messages.stdout
```

Note the files can have any name so long as the thing extension and file format is correct.

### Messages Format

The messages file should be formatted as a TSV (tab separated values). It should have columns for timestamp, data format and the data itself as a JSON dump. An example is provided below

```
1698887338.135741   application/json	{"username": "/tordata/config/group_1_user_0", "text": "An example message"}
1698887338.2363834	application/json	{"username": "/tordata/config/group_0_user_2", "text": "Another message"}
1698887338.6288576	application/json	{"username": "/tordata/config/group_1_user_0", "text": "A third message"}
```

### PCAP names

PCAP files can have any name but their name should match with the configuration used. For example, the provided example configuration file (example_config_small.yaml) contains the section:
```
scope_config:
  - [".*isp-1.csv", "ISP1", none, [True, False]]
  - ["(.*root).*.csv", "root", dot_filter, [True, True] ]
```

Each value in the `scope_config` list defines a different grouping of PCAPs (each PCAP group will be treated as if it were a single PCAP). 
The first value (e.g. ".*isp-1.csv") is a quoted regex of the pcap files in that group/scope (note the csv extension should be used instead of the .pcap extension. this format change will happen during proccessing automatically).
The second value is friendly name for the scope displayed in the GUI. 
The third and fourth parameters are special arguments that can be applied for certain scopes. If the scope only has DNS data then `dot_filter` should be used (captures all DNS traffic not just DoT). The last parameter should be set to `[True, False]` in almost every case. Setting this to `[True, True]` will dramatically increase processing time on most analysis and does not generally improve performance.

## Cleaning up runs from dashboard

- Enter Redis container by running `docker exec -it <container_name> bash`
- Run `redis-cli` to enter the Redis CLI
- We need to remove the following from Redis (here `<experiment-name>` is the name of the experiment we see in the dashboard)

  - `*-log-list` log list for the experiment
    - run `hget REDIS_DASHBOARD_EXPERIMENTS_SET:<experiment-name> logListKey` to view the key
    - run `del <key>` to delete the key with the name from above command
  - `REDIS_DASHBOARD_EXPERIMENTS_SET:<experiment-name>` hash
    - run `del REDIS_DASHBOARD_EXPERIMENTS_SET:<experiment-name>`
  - remove the experiment from the set of experiments
    - run `srem REDIS_DASHBOARD_EXPERIMENTS_SET <experiment-name>`

- Exit the Redis CLI and the container
- remove results for the experiment from the `results` directory in processor-common-folder (if it exists)
