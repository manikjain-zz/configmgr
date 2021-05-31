import pytest
from configmgr_methods import ssh_connection, close_cmd_channel
from yaml import load
from yaml.loader import FullLoader

with open('test_config.yaml', 'r') as f:
    config = load(f, Loader=FullLoader)

# Get list of hosts from the config
host = config["hosts"][0]
# Get password value from the config
password = config["auth"]["password"]
# Get host_keys_path value from the config
host_keys_path = config["auth"]["host_keys_path"]   

def test_ssh_connection():
    # Establish an SSHclient channel for all the hosts
    client = ssh_connection(host, password, host_keys_path)
    stdin, stdout, stderr = client.exec_command(f'echo')
    result = stdout.channel.recv_exit_status()
    close_cmd_channel(stdin, stdout, stderr)
    client.close()

    assert result == 0

def test_package_installation():
    packages = ' '.join(map(str, config["package"]["name"]))

    client = ssh_connection(host, password, host_keys_path)
    stdin, stdout, stderr = client.exec_command(f'apt update && apt install -y {packages}')
    result = stdout.channel.recv_exit_status()
    close_cmd_channel(stdin, stdout, stderr)
    stdin, stdout, stderr = client.exec_command(f'apt remove -y {packages} && apt autoremove -y')
    close_cmd_channel(stdin, stdout, stderr)
    client.close()

    assert result == 0

def test_file_creation():
    content = config["file"]["content"]
    permissions = config["file"]["permissions"]
    name = config["file"]["name"]
    path = config["file"]["path"]
    
    client = ssh_connection(host, password, host_keys_path)
    stdin, stdout, stderr = client.exec_command(f'echo \'{content}\' > {path}/{name} && chown {permissions["user"]}:{permissions["group"]} {path}/{name} && chmod {permissions["access"]} {path}/{name}')
    result = stdout.channel.recv_exit_status()
    close_cmd_channel(stdin, stdout, stderr)
    stdin, stdout, stderr = client.exec_command(f'rm -f {path}/{name}')
    close_cmd_channel(stdin, stdout, stderr)
    client.close()

    assert result == 0

def test_restart_service():
    service_name = config["package"]["restart_service"]
    
    client = ssh_connection(host, password, host_keys_path)
    stdin, stdout, stderr = client.exec_command(f'systemctl restart {service_name}.service')
    result = stdout.channel.recv_exit_status()
    close_cmd_channel(stdin, stdout, stderr)
    client.close()

    assert result == 0