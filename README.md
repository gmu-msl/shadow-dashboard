# Shadow Dashboard

## Steps to update the deployment

Run `make all` from the root of the repository from `sr4s5.mesa.gmu.edu`. This will build the images, push them to the private docker registry and then update the swarm.

> You must be logged into docker on `sr4s5.mesa.gmu.edu` for this to run correctly.

> If running from a different server cluster the make file and dockerfiles must be updated with the correct docker registry and images to run.

### Manually

- First update the docker image `sr4s5.mesa.gmu.edu:5000/shadow-dashboard:amd64` by building the docker image from the `Dockerfile` in the `shadow-dashboard` directory. Run `docker build . -t sr4s5.mesa.gmu.edu:5000/shadow-dashboard:amd64 --platform linux/amd64` for this
- Push the updated docker image to the registry by running `docker push sr4s5.mesa.gmu.edu:5000/shadow-dashboard:amd64`
- Log in to sr4s5 and run `docker service update shadow-dashboard_dashboard --with-registry-auth --image sr4s5.mesa.gmu.edu:5000/shadow-dashboard:amd64` This will update the deployment with the new image

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
