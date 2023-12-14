.DEFAULT_GOAL:=help
ROOT_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

##@ Test
.PHONY: test-top
test-top:  ## spawn `top` in a subprocess via `spty.spawn`
	docker run --rm -it --entrypoint=bash --name spty-test-top \
	-v ${ROOT_DIR}/../:/tmp/simple-pty \
	python:3.10.13 /tmp/simple-pty/intergration/init.sh /tmp/simple-pty/intergration/test-top/test.py



##@ Misc
.PHONY: help
help:  ## Show this message
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
