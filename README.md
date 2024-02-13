# Shadow Dashboard

## Steps to update the deployment

- First update the docker image `sr4s5.mesa.gmu.edu:5000/shadow-dashboard:amd64` by building the docker image from the `Dockerfile` in the `shadow-dashboard` directory. Run `docker build . -t sr4s5.mesa.gmu.edu:5000/shadow-dashboard:amd64 --platform linux/amd64` for this
- Push the updated docker image to the registry by running `docker push sr4s5.mesa.gmu.edu:5000/shadow-dashboard:amd64`
- Log in to sr4s5 and run `docker service update shadow-dashboard_dashboard --with-registry-auth --image sr4s5.mesa.gmu.edu:5000/shadow-dashboard:amd64` This will update the deployment with the new image
