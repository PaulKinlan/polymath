
import argparse
import json
import os

DEFAULT_CONFIG_FILE = 'directory.SECRET.json'

# A map of property name to example
HOST_SETTABLE_PROPERTIES = {
    'endpoint': 'https://example.com',
    'token': 'sk-SECRET-token',
    'dev_endpoint': 'http://127.0.0.1:8080'
}

# TODO: factor to share with host.py
BOOLEAN_STRINGS = {
    'true': True,
    'false': False,
    '0': False,
    '1': True
}

# TODO: factor to share with host.py
def save_config_file(data, access_file=DEFAULT_CONFIG_FILE):
    with open(access_file, 'w') as f:
        json.dump(data, f, indent='\t')


# TODO: factor to share with host.py
def load_config_file(access_file=DEFAULT_CONFIG_FILE):
    data = {}
    if os.path.exists(access_file):
        with open(access_file, 'r') as f:
            data = json.load(f)
    return data

# TODO: factor to share with host.py
def set_property_in_data(data, property, value):
    property_parts = property.split('.')
    if len(property_parts) == 1:
        if property in data and data[property] == value:
            return False
        data[property] = value
        return True
    first_property_part = property_parts[0]
    rest = '.'.join(property_parts[1:])
    if first_property_part not in data:
        data[first_property_part] = {}
    return set_property_in_data(data[first_property_part], rest, value)
        
# TODO: factor to share with host.py
def unset_property_in_data(data, property):
    """
    Returns True if it made a change, False if not
    """
    property_parts = property.split('.')
    if len(property_parts) == 1:
        if property in data:
            del data[property]
            return True
        return False
    first_property_part = property_parts[0]
    rest = '.'.join(property_parts[1:])
    if first_property_part not in data:
        return False
    result = unset_property_in_data(data[first_property_part], rest)
    if len(data[first_property_part]) == 0:
        del data[first_property_part]
    return result


def host_property(host_name, property):
    return 'hosts.' + host_name + '.' + property


def host_set_command(args):
    property = host_property(args.host, args.property)
    value = args.value
    original_value = args.value
    config_for_property = HOST_SETTABLE_PROPERTIES[args.property]
    access_file = args.file
    if isinstance(config_for_property, bool):
        value = value.lower()
        if value not in BOOLEAN_STRINGS:
            known_strings = list(BOOLEAN_STRINGS.keys())
            raise Exception(f'Unknown value for a boolean property: {value} (known values are {known_strings})')
        value = BOOLEAN_STRINGS[value]
    elif isinstance(config_for_property, int):
        value = int(value)
    data = load_config_file(access_file)
    changes_made = set_property_in_data(data, property, value)
    if not changes_made:
        print(f'{property} was already set to {value} so no changes to be made.')
        return
    save_config_file(data, access_file=access_file)
    print(f'Set {property} to {original_value}')


def host_unset_command(args):
    property = host_property(args.host, args.property)
    access_file = args.file
    data = load_config_file(access_file)
    made_change = unset_property_in_data(data, property)
    if not made_change:
        print(f'{property} was not configured, nothing to do')
        return
    save_config_file(data, access_file=access_file)
    print(f'Unset {property}')


parser = argparse.ArgumentParser()

base_parser = argparse.ArgumentParser(add_help=False)
base_parser.add_argument("--file", help="The config file to operate on", default=DEFAULT_CONFIG_FILE)

sub_parser = parser.add_subparsers(title='action')
sub_parser.required = True
host_set_parser = sub_parser.add_parser('set', parents=[base_parser])
host_set_parser.add_argument('host', help='The vanity name of the host to set the property on')
host_set_parser.add_argument('property', help='The name of the property to set', choices=list(HOST_SETTABLE_PROPERTIES.keys()))
host_set_parser.add_argument('value', help='The value to set')
host_set_parser.set_defaults(func=host_set_command)
host_unset_parser = sub_parser.add_parser('unset', parents=[base_parser])
host_unset_parser.add_argument('host', help='The vanity name of the host to unset the property on')
host_unset_parser.add_argument('property', help='The name of the property to unset', choices=list(HOST_SETTABLE_PROPERTIES.keys()))
host_unset_parser.set_defaults(func=host_unset_command)

args = parser.parse_args()
args.func(args)