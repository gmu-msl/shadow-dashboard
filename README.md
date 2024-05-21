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

The docker configuration provided requires access to a docker registry, nfs storage with read and write access and a docker swarm cluster. The user must have read and write access to the docker registry and be able to deploy docker compose configurations to the docker swarm. The variables for these can be found in the `.env` file in the root of the project. Additionally, DASHBOARD_HOSTNAME in `.env` should be set to the hostname of the machine where the dashboard will be hosted on.

> Note: Internet access is required to build the docker images

> If running from inside of GMU CARE: No changes are needed if you are running from `sr4s5.mesa.gmu.edu`.

### Steps to update the deployment

Run `make all` from the root of the repository. This machine must have access to a docker registry. This will build the images, push them to the private docker registry and then update the docker swarm.

The dashboard will be available on `${DASHBOARD_HOSTNAME}:8080`.

### Manually

- First update the docker image `shadow-dashboard:amd64` by building the docker image from the `Dockerfile` in the `shadow-dashboard` directory. Run `docker build . -t ${DOCKER_REGISTRY}/shadow-dashboard:amd64 --platform linux/amd64` for this
- Push the updated docker image to the registry by running `docker push ${DOCKER_REGISTRY}/shadow-dashboard:amd64`
- Log in to a machine that has access to the docker registry and cluster. Run `docker service update shadow-dashboard_dashboard --with-registry-auth --image ${DOCKER_REGISTRY}/shadow-dashboard:amd64` This will update the deployment with the new image

## Cleaning up runs from dashboard

- Enter redis container by running `docker exec -it <container_name> bash`
- Run `redis-cli` to enter the redis cli
- We need to remove the following from redis (here `<experiment-name>` is the name of the experiment we see in the dashboard)

  - `*-log-list` log list for the experiment
    - run `hget REDIS_DASHBOARD_EXPERIMENTS_SET:<experiment-name> logListKey` to view the key
    - run `del <key>` to delete the key with the name from above command
  - `REDIS_DASHBOARD_EXPERIMENTS_SET:<experiment-name>` hash
    - run `del REDIS_DASHBOARD_EXPERIMENTS_SET:<experiment-name>`
  - remove the experiment from the set of experiments
    - run `srem REDIS_DASHBOARD_EXPERIMENTS_SET <experiment-name>`

- Exit the redis cli and the container
- remove results for the experiment from the `results` directory in processor-common-folder (if it exists)
