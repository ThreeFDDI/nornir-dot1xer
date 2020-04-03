#!/usr/local/bin/python3
'''
This script is to apply dot1x config to Catalyst switch stacks
'''

from nornir import InitNornir
from nornir.core.filter import F
from nornir.plugins.functions.text import print_result
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.tasks import text
from pprint import pprint as pp
from ttp import ttp


# Get info from switches
def get_info(task):

    # get software version; use TextFSM
    sh_version = task.run(
        task=netmiko_send_command,
        command_string="show version",
        use_textfsm=True,
    )

    # save show version output to task.host
    task.host['sh_version'] = sh_version.result[0]
    # pull model from show version
    sw_model = task.host['sh_version']['hardware'][0].split("-")
    # save model to task.host
    task.host['sw_model'] = sw_model[1]

    # get interfaces; use TextFSM
    interfaces = task.run(
        task=netmiko_send_command,
        command_string="show interface switchport",
        use_textfsm=True,
    )

    # save interfaces to task.host
    task.host['intfs'] = interfaces.result
    

# Switch model decison
def apply_dot1x(task):

    # print hostname and switch model
    print(task.host)
    print(task.host['sw_model'])

    # choose template based on switch model
    if "3750" in task.host['sw_model']:
        # 3750's use IBNSv1
        ibnsv1_dot1x(task)

    else:
        # all other switches use IBNSv2
        ibnsv2_dot1x(task)


# Apply IBNSv1 dot1x config template
def ibnsv1_dot1x(task):

    # testing prints
    print(task.host['ise_key'])
    print(task.host['vlans'])
    print(task.host['ise_pri'])
    print(task.host['ise_sec'])
    print(task.host['excluded_intf'])
    print(task.host['uplinks'])

    # init lists of interfaces
    access_interfaces = []
    uplink_interfaces = []

    # iterate over all interfaces 
    for intf in task.host['intfs']:

        # uplinks
        if intf['interface'] in task.host['uplinks']:
            uplink_interfaces.append(intf['interface'])

        # other non-excluded access ports 
        elif intf['interface'] not in task.host['excluded_intf']:
            continue

        elif intf['interface'] in task.host['excluded_intf']:

            access_interfaces.append(
                {
                    'interface': intf['interface'],
                    'access_vlan': intf['access_vlan']
                }
            )

    task.host['uplink_interfaces'] = uplink_interfaces

    task.host['uplink_intf_cfg'] = task.run(
        task=text.template_file, 
        template="IBNS_uplink_intf.j2", 
        path="templates/", 
        **task.host
    )
    task.host['access_interfaces'] = access_interfaces

    task.host['access_intf_cfg'] = task.run(
        task=text.template_file, 
        template="IBNSv1_access_intf.j2", 
        path="templates/", 
        **task.host
    )

    print(uplink_interfaces)
    print(task.host['uplink_intf_cfg'].result)
    print(task.host['access_intf_cfg'].result)


# Apply IBNSv2 dot1x config templates
def ibnsv2_dot1x(task):
    _stuff = None


# Main function
def main():
    # initialize The Norn
    nr = InitNornir()
    # filter The Norn
    nr = nr.filter(platform="cisco_ios")
    # run The Norn to get info
    nr.run(task=get_info)
    # run The Norn to apply dot1x config
    nr.run(task=apply_dot1x)


if __name__ == "__main__":
    main()
