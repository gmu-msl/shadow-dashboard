_BUILD_ARGS_RELEASE_TAG ?= latest
_BUILD_ARGS_DOCKERFILE ?= Dockerfile
_BUILD_ARGS_NAME ?= DEFAULT

all: 
	$(MAKE) update_dashboard
	$(MAKE) update_evaluator

release_all: 
	$(MAKE) release_dashboard
	$(MAKE) release_evaluator

_builder:
	docker build -t sr4s5.mesa.gmu.edu:5000/shadow-${_BUILD_ARGS_NAME}:amd64 --platform linux/amd64 -f ${_BUILD_ARGS_DOCKERFILE} .
 
_pusher:
	docker push sr4s5.mesa.gmu.edu:5000/shadow-${_BUILD_ARGS_NAME}:amd64
 
_releaser:
	docker service update shadow-dashboard_${_BUILD_ARGS_NAME} --with-registry-auth --image sr4s5.mesa.gmu.edu:5000/shadow-${_BUILD_ARGS_NAME}:amd64 --force

build:
	$(MAKE) _builder
 
push:
	$(MAKE) _pusher
 
release:
	$(MAKE) _releaser

update:
	$(MAKE) _builder
	$(MAKE) _pusher
	$(MAKE) _releaser

build_%:
	$(MAKE) _builder -e _BUILD_ARGS_DOCKERFILE="Dockerfile.$*" -e _BUILD_ARGS_NAME="$*"
 
push_%:
	$(MAKE) _pusher -e _BUILD_ARGS_NAME="$*"
 
release_%:
	$(MAKE) _releaser -e _BUILD_ARGS_NAME="$*" 

update_%:
	$(MAKE) build_$*
	$(MAKE) push_$*
	$(MAKE) release_$*
