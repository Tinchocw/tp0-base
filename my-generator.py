import yaml
import sys

class MyDumper(yaml.Dumper):

    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)
    


def add_clients(num_clients, data):
    for i in range(1, num_clients + 1):
        client_name = f'client{i}'
        data['services'][client_name] = {
            'container_name': client_name,
            'image': 'client:latest',
            'entrypoint': '/client',
            'environment': [
                f'CLI_ID={i}',
                'CLI_LOG_LEVEL=DEBUG'
            ],
            'networks': ['testing_net'],
            'depends_on': ['server']
        }
    

def generate_docker_compose(num_clients, output_file):
    data = {
        'name': 'tp0',
        'services': {
            'server': {
                'container_name': 'server',
                'image': 'server:latest',
                'entrypoint': 'python3 /main.py',
                'environment': [
                    'PYTHONUNBUFFERED=1',
                    'LOGGING_LEVEL=DEBUG'
                ],
                'networks': ['testing_net']
            }
        },
        'networks': {
            'testing_net': {
                'ipam': {
                    'driver': 'default',
                    'config': [
                        {'subnet': '172.25.125.0/24'}
                    ]
                }
            }
        }
    }

    add_clients(num_clients, data)

    with open(output_file, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, Dumper=MyDumper, sort_keys=False, indent=2)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python3 mi-generador.py <output_file> <num_clients>')
        sys.exit(1)

    output_file = sys.argv[1]
    num_clients = int(sys.argv[2])
    
    generate_docker_compose(num_clients, output_file)

    

