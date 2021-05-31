'''
    File name: configmgr_methods.py
    Author: Manik Jain
    Date created: 31/May/2020
    Python Version: 3.8
'''

# Import modules
from paramiko import SSHClient, AutoAddPolicy
from rich.console import Console

# Initialize console from rich to use the print statement
console = Console()

# Define a function to establish an SSH connection
# and open an SSHclient channel
def ssh_connection(host, pw, host_keys_path):
    client = SSHClient()
    client.load_host_keys(host_keys_path)
    client.load_system_host_keys()
    client.set_missing_host_key_policy(AutoAddPolicy())
    client.connect(host, username='root', password=pw)
    return client

# Define a function to close the command execution channel
def close_cmd_channel(stdin, stdout, stderr):
    stdin.close()
    stdout.close()
    stderr.close()

# Define a function to handle installation and removal of packages
def install_packages(host, client, packages, state):
    no_of_packages = len(packages.split())
    # Check for currently installed packages
    stdin, stdout, stderr = client.exec_command(f'apt -qq list --installed {packages} | wc -l')
    if stdout.channel.recv_exit_status() == 0:
        installed_packages = int(stdout.read().decode("utf8"))
    else:
        console.print(f'{host} [ [red]error[/] ] => Error checking packages {packages}: {stderr.read().decode("utf8")}')
    close_cmd_channel(stdin, stdout, stderr)

    # Check for the value of 'state' set in config and proceed accordingly
    # Remove packages if 'state' is set to absent
    if state == "absent":
        # If the packages requested to be removed are already missing
        if (installed_packages == 0):
            console.print(f'{host} [ [green]unchanged[/] ] => Packages {packages} are already removed')
        # If packages are found, remove them
        else:
            stdin, stdout, stderr = client.exec_command(f'apt remove -y {packages} && apt autoremove -y')

            if stdout.channel.recv_exit_status() == 0:
                console.print(f'{host} [ [yellow]changed[/] ] => Removed packages {packages} successfully!')
            else:
                console.print(f'{host} [ [red]error[/] ] => Error removing packages {packages}: {stderr.read().decode("utf8")}')
            close_cmd_channel(stdin, stdout, stderr)
    # Install or modify packages if 'state' is set to present
    elif state == "present":
        # If packages are already installed as requested in the config, do nothing
        if (no_of_packages == installed_packages):
            console.print(f'{host} [ [green]unchanged[/] ] => Packages {packages} are already installed')
        # If packages are not installed, install them
        else:
            stdin, stdout, stderr = client.exec_command(f'apt update && apt install -y {packages}')
            if stdout.channel.recv_exit_status() == 0:
                console.print(f'{host} [ [yellow]changed[/] ] => Installed packages {packages} successfully!')
            else:
                console.print(f'{host} [ [red]error[/] ] => Error installing packages {packages}: {stderr.read().decode("utf8")}')
            close_cmd_channel(stdin, stdout, stderr)

# Define a function to handle restarting of a service
def restart_service(host, client, name):
    # Execute command to restart a service
    stdin, stdout, stderr = client.exec_command(f'systemctl restart {name}.service')

    if stdout.channel.recv_exit_status() == 0:
        console.print(f'{host} [ [yellow]changed[/] ] => Restarted the {name} service')
    else:
        console.print(f'{host}[ [red]error[/] ] => Error restarting {name} service: {stderr.read().decode("utf8")}')

    close_cmd_channel(stdin, stdout, stderr)

# Define a function to handle file creation, modification and removal
def file(host, client, path, name, content, permissions, state):
    # Check if file exists already
    stdin, stdout, stderr = client.exec_command(f'if [ -e {path}/{name} ]; then echo 0; else echo 1; fi')
    if stdout.channel.recv_exit_status() == 0:
        file_exists = int(stdout.read().decode("utf8"))
        close_cmd_channel(stdin, stdout, stderr)
        # Check for the value of 'state' key set in the config and proceed accordingly
        # Create or modify file if 'state' set to present
        if state == "present":
            # If the file does not exist, create it
            if (file_exists == 1):
                stdin, stdout, stderr = client.exec_command(f'echo \'{content}\' > {path}/{name} && chown {permissions["user"]}:{permissions["group"]} {path}/{name} && chmod {permissions["access"]} {path}/{name}')
                if stdout.channel.recv_exit_status() == 0:
                    console.print(f'{host} [ [yellow]changed[/] ] => File created at {path}/{name} with content as follows: \n{content}\n and owner: {permissions["user"]}, group: {permissions["group"]}, access: {permissions["access"]}')
                else:
                    console.print(f'{host} [ [red]error[/] ] => Error creating file at {path}/{name}: {stderr.read().decode("utf8")}')
                close_cmd_channel(stdin, stdout, stderr)
            # If the file exists, check for differing permissions and file content
            elif (file_exists == 0):
                permissions_list = [value for value in permissions.values()]
                permissions_str =  ' '.join(map(str, permissions_list))
                stdin, stdout, stderr = client.exec_command(f'stat -c "%U %G %a" {path}/{name}')
                if stdout.channel.recv_exit_status() == 0:
                    current_perms = str(stdout.read().decode("utf8").rstrip())
                else:
                    console.print(f'{host} [ [red]error[/] ] => File check failed: {stderr.read().decode("utf8")}')
                current_perms_formatted = current_perms.replace(' ',',')
                close_cmd_channel(stdin, stdout, stderr)
                # Check the existing file for any different content than requested
                stdin, stdout, stderr = client.exec_command(f'echo \'{content}\' > {path}/{name}.test && cmp --silent {path}/{name} {path}/{name}.test && echo 0 || echo 1; rm -f {path}/{name}.test')
                if stdout.channel.recv_exit_status() == 0:                
                    file_diff = int(stdout.read().decode("utf8"))
                else:
                    console.print(f'{host} [ [red]error[/] ] => File check failed: {stderr.read().decode("utf8")}')     
                close_cmd_channel(stdin, stdout, stderr)
                
                # Compare existing permissions on the file with permissions requested
                # If the current file permissions are the same as requested
                if (current_perms == permissions_str):
                    # If file content requested differs
                    if file_diff == 1:
                        stdin, stdout, stderr = client.exec_command(f'echo \'{content}\' > {path}/{name}')
                        if stdout.channel.recv_exit_status() == 0:
                            console.print(f'{host} [ [yellow]changed[/] ] => File already exists at {path}/{name} with different content and required access permissions set to {current_perms_formatted} (user,group,access). Content as follows: \n{content}\n copied over to {path}/{name}')    
                        else:
                            console.print(f'{host} [ [red]error[/] ] => File already exists at {path}/{name} with different content and required access permissions set to {current_perms_formatted} (user,group,access). Error copying new content over to {path}/{name}: {stderr.read().decode("utf8")}')
                        close_cmd_channel(stdin, stdout, stderr)
                    # If file content does not differ, no changes required
                    elif file_diff == 0:
                        console.print(f'{host} [ [green]unchanged[/] ] => File already exists at {path}/{name} with the required content and access permissions set to {permissions}')    
                # If current file permissions differ from the requested permissions
                else:
                    # If file content also differs
                    if file_diff == 1:
                        stdin, stdout, stderr = client.exec_command(f'echo \'{content}\' > {path}/{name} && chown {permissions["user"]}:{permissions["group"]} {path}/{name} && chmod {permissions["access"]} {path}/{name}')
                        if stdout.channel.recv_exit_status() == 0:
                            console.print(f'{host} [ [yellow]changed[/] ] => File already exists at {path}/{name} with different content and access permissions set to {current_perms_formatted} (user,group,access). Access permissions have been modified to match {permissions} and content as follows: \n{content}\n copied over to {path}/{name}')    
                        else:
                            console.print(f'{host} [ [red]error[/] ] => File already exists at {path}/{name} with different content and access permissions set to {current_perms_formatted} (user,group,access). Error modifying permissions and copying new content over to {path}/{name}: {stderr.read().decode("utf8")}')
                        close_cmd_channel(stdin, stdout, stderr)
                    # If file content does not differ
                    elif file_diff == 0:
                        stdin, stdout, stderr = client.exec_command(f'chown {permissions["user"]}:{permissions["group"]} {path}/{name} && chmod {permissions["access"]} {path}/{name}')
                        if stdout.channel.recv_exit_status() == 0:
                            console.print(f'{host} [ [yellow]changed[/] ] => File already exists at {path}/{name} with the required content and different access permissions set to {current_perms_formatted} (user,group,access). Access permissions have been modified to match {permissions}')    
                        else:
                            console.print(f'{host} [ [red]error[/] ] => File already exists at {path}/{name} with the required content and different access permissions set to {current_perms_formatted} (user,group,access). Error modifying permissions on {path}/{name}: {stderr.read().decode("utf8")}')
                        close_cmd_channel(stdin, stdout, stderr)
        # Remove file if 'state' is set to absent
        elif state == "absent":
            # If file exists, remove it
            if (file_exists == 0):
                stdin, stdout, stderr = client.exec_command(f'rm -f {path}/{name}')

                if stdout.channel.recv_exit_status() == 0:
                    console.print(f'{host} [ [yellow]changed[/] ] => File removed at {path}/{name}')
                else:
                    console.print(f'{host} [ [red]error[/] ] => Error removing file at {path}/{name}: {stderr.read().decode("utf8")}')

                close_cmd_channel(stdin, stdout, stderr) 
            # If file does not exist, do nothing
            elif file_exists == 1:
                console.print(f'{host} [ [green]unchanged[/] ] => File not found at {path}/{name}')
    else:
        console.print(f'{host} [ [red]error[/] ] => Something went wrong, file check failed: {stderr.read().decode("utf8")}')
        close_cmd_channel(stdin, stdout, stderr)