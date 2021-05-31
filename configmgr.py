#!/usr/bin/env python3

'''
    File name: configmgr.py
    Author: Manik Jain
    Date created: 31/May/2020
    Python Version: 3.8
''' 

# Import modules
from configmgr_methods import ssh_connection, install_packages, file, restart_service
from rich.console import Console
from yaml import load
from yaml.loader import FullLoader
from cerberus import Validator

# Define a main execution function
def main():
    # Initialise console from rich library to use the print statement
    console = Console()

    # Open and load config.yaml from the current directory
    with open('config.yaml', 'r') as f:
        config = load(f, Loader=FullLoader)

    # Open and load the config_schema.py from the current directory for YAML linting purposes
    schema = eval(open('./config_schema.py', 'r').read())
    # Use the schema from above for validation
    v = Validator(schema)
    # If config.yaml is found to be valid, proceed
    if v.validate(config, schema):
        # Get list of hosts from the config
        hosts = config["hosts"]
        # Get password value from the config
        password = config["auth"]["password"]
        # Get host_keys_path value from the config
        host_keys_path = config["auth"]["host_keys_path"]

        # Create a dictionary to store the SSHclient channel objects for the hosts
        clients = {}

        # Establish an SSHclient channel for all the hosts and store it in clients dict
        for host in hosts:
            clients[host] = ssh_connection(host, password, host_keys_path)

        # Check if 'package' related operations are requested in the config
        if 'package' in config:
            packages = ' '.join(map(str, config["package"]["name"]))

            if config["package"]["state"] == "present":
                console.print(f'\n[bold][Install/Remove packages] Install packages {packages}[/]\n')
            elif config["package"]["state"] == "absent":
                console.print(f'\n[bold][Install/Remove packages] Remove packages {packages}[/]\n')

            # Execute install_packages function for all hosts   
            for client in clients:
                install_packages(client, clients[client], packages, config["package"]["state"])
                # Check if restarting of a service was requested alongside, and the execute the same
                if 'restart_service' in config["package"]:
                    restart_service(client, clients[client], config["package"]["restart_service"])

        # Check if 'file' related operations are requested in the config
        if 'file' in config:

            if config["file"]["state"] == "present":
                console.print(f'\n[bold][Add/Remove file] Add file {config["file"]["path"]}/{config["file"]["name"]}[/]\n')
            elif config["file"]["state"] == "absent":
                console.print(f'\n[bold][Add/Remove file] Remove file {config["file"]["path"]}/{config["file"]["name"]}[/]\n')
            
            # Execute file function for all hosts
            for client in clients:
                if config["file"]["state"] == "present":
                    file(client, clients[client], config["file"]["path"], config["file"]["name"], config["file"]["content"], {'user': config["file"]["permissions"]["user"], 'group': config["file"]["permissions"]["group"], 'access': config["file"]["permissions"]["access"]}, config["file"]["state"])
                elif config["file"]["state"] == "absent":
                    file(client, clients[client], config["file"]["path"], config["file"]["name"], config["file"]["content"], {}, config["file"]["state"])
                if 'restart_service' in config["file"]:
                    restart_service(client, clients[client], config["file"]["restart_service"])

        # Close the SSHclient channels for all hosts
        for client in clients:
            clients[client].close()
        
        console.print()
    # If config.yaml is found to have errors
    else:
        console.print(f'Error validating config: {v.errors}')

# Execute the main function
main()
