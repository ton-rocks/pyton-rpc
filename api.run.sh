docker volume create ton-rocks-api-vol

core_count=$((`grep processor /proc/cpuinfo | wc -l` * 2 + 1 ))
global_config=https://raw.githubusercontent.com/ton-rocks/network-config/master/test.rocks.config.json

docker run -d --name ton-rocks-api0 --mount source=ton-rocks-api-vol,target=/var/ton-work --network host -e "core_count=$core_count" -e "global_config=$global_config" -it ton-rocks-api-image 
