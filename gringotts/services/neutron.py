import time
from oslo.config import cfg

from gringotts import utils
from gringotts import constants as const

from gringotts.openstack.common import log

from gringotts.services import wrap_exception
from gringotts.services import Resource
from gringotts.services import keystone as ks_client
from neutronclient.v2_0 import client as neutron_client
from neutronclient.common.exceptions import NeutronClientException
from gringotts.openstack.common import timeutils


LOG = log.getLogger(__name__)


OPTS = [
    cfg.BoolOpt('reserve_fip',
                default=True,
                help="Reserve floating ip or not when account owed")
]

cfg.CONF.register_opts(OPTS)


class FloatingIp(Resource):
    def to_message(self):
        msg = {
            'event_type': 'floatingip.create.end.again',
            'payload': {
                'floatingip': {
                    'id': self.id,
                    'uos:name': self.name,
                    'rate_limit': self.size,
                    'tenant_id': self.project_id
                }
            },
           'timestamp': self.created_at
        }
        return msg


class Router(Resource):
    def to_message(self):
        msg = {
            'event_type': 'router.create.end.again',
            'payload': {
                'router': {
                    'id': self.id,
                    'name': self.name,
                    'tenant_id': self.project_id
                }
            },
            'timestamp': self.created_at
        }
        return msg


class Listener(Resource):
    def to_message(self):
        msg = {
            'event_type': 'listener.create.end',
            'payload': {
                'listener': {
                    'id': self.id,
                    'name': self.name,
                    'admin_state_up': self.admin_state_up,
                    'connection_limit': self.connection_limit,
                    'tenant_id': self.project_id
                }
            },
            'timestamp': self.created_at
        }
        return msg


class Network(Resource):
    pass


class Port(Resource):
    pass


def get_neutronclient(region_name=None):
    endpoint = ks_client.get_endpoint(region_name, 'network')
    auth_token = ks_client.get_token()
    c = neutron_client.Client(token=auth_token,
                              endpoint_url=endpoint)
    return c


@wrap_exception(exc_type='list')
def subnet_list(project_id, region_name=None):
    client = get_neutronclient(region_name)
    subnets = client.list_subnets(tenant_id=project_id).get('subnets')
    return subnets


@wrap_exception(exc_type='list')
def port_list(project_id, region_name=None, device_id=None, project_name=None):
    client = get_neutronclient(region_name)
    if device_id:
        ports = client.list_ports(tenant_id=project_id,
                                  device_id=device_id).get('ports')
    else:
        ports = client.list_ports(tenant_id=project_id).get('ports')

    formatted_ports = []
    for port in ports:
        status = utils.transform_status(port['status'])
        formatted_ports.append(Port(id=port['id'],
                                    name=port['name'],
                                    is_bill=False,
                                    resource_type='port',
                                    status=status,
                                    project_id=port['tenant_id'],
                                    project_name=project_name,
                                    original_status=port['status']))

    return formatted_ports


@wrap_exception(exc_type='list')
def network_list(project_id, region_name=None, project_name=None):
    client = get_neutronclient(region_name)
    networks = client.list_networks(tenant_id=project_id).get('networks')
    formatted_networks = []
    for network in networks:
        status = utils.transform_status(network['status'])
        formatted_networks.append(Network(id=network['id'],
                                          name=network['name'],
                                          is_bill=False,
                                          resource_type='network',
                                          status=status,
                                          project_id=network['tenant_id'],
                                          project_name=project_name,
                                          original_status=network['status']))
    return formatted_networks


@wrap_exception(exc_type='get')
def floatingip_get(fip_id, region_name=None):
    try:
        fip = get_neutronclient(region_name).show_floatingip(fip_id).get('floatingip')
    except NeutronClientException:
        return None
    status = utils.transform_status(fip['status'])
    return FloatingIp(id=fip['id'],
                      name=fip['uos:name'],
                      resource_type=const.RESOURCE_FLOATINGIP,
                      status=status,
                      original_status=fip['status'],
                      is_reserved=True)


@wrap_exception(exc_type='get')
def router_get(router_id, region_name=None):
    try:
        router = get_neutronclient(region_name).show_router(router_id).get('router')
    except NeutronClientException:
        return None
    status = utils.transform_status(router['status'])
    return Router(id=router['id'],
                  name=router['name'],
                  resource_type=const.RESOURCE_ROUTER,
                  status=status,
                  original_status=router['status'])


@wrap_exception(exc_type='list')
def floatingip_list(project_id, region_name=None, project_name=None):
    client = get_neutronclient(region_name)
    if project_id:
        fips = client.list_floatingips(tenant_id=project_id).get('floatingips')
    else:
        fips = client.list_floatingips().get('floatingips')
    formatted_fips = []
    for fip in fips:
        created_at = utils.format_datetime(fip['created_at'])
        status = utils.transform_status(fip['status'])
        formatted_fips.append(FloatingIp(id=fip['id'],
                                         name=fip['uos:name'],
                                         size=fip['rate_limit'],
                                         project_id=fip['tenant_id'],
                                         project_name=project_name,
                                         resource_type=const.RESOURCE_FLOATINGIP,
                                         status=status,
                                         original_status=fip['status'],
                                         created_at=created_at))
    return formatted_fips


@wrap_exception(exc_type='list')
def router_list(project_id, region_name=None, project_name=None):
    client = get_neutronclient(region_name)
    if project_id:
        routers = client.list_routers(tenant_id=project_id).get('routers')
    else:
        routers = client.list_routers().get('routers')
    formatted_routers = []
    for router in routers:
        created_at = utils.format_datetime(router['created_at'])
        status = utils.transform_status(router['status'])
        formatted_routers.append(Router(id=router['id'],
                                        name=router['name'],
                                        project_id=router['tenant_id'],
                                        project_name=project_name,
                                        resource_type=const.RESOURCE_ROUTER,
                                        status=status,
                                        original_status=router['status'],
                                        created_at=created_at))
    return formatted_routers


@wrap_exception(exc_type='bulk')
def delete_fips(project_id, region_name=None):
    client = get_neutronclient(region_name)

    # Get floating ips
    fips = client.list_floatingips(tenant_id=project_id)
    fips = fips.get('floatingips')

    # Disassociate these floating ips
    update_dict = {'port_id': None}
    for fip in fips:
        client.update_floatingip(fip['id'],
                                 {'floatingip': update_dict})

    # Release these floating ips
    for fip in fips:
        client.delete_floatingip(fip['id'])
        LOG.warn("Delete floatingip: %s" % fip['id'])


@wrap_exception(exc_type='bulk')
def delete_routers(project_id, region_name=None):
    client = get_neutronclient(region_name)

    routers = client.list_routers(tenant_id=project_id).get('routers')
    for router in routers:
        # Remove gateway
        client.remove_gateway_router(router['id'])

        # Get interfaces of this router
        ports = client.list_ports(tenant_id=project_id,
                                  device_id=router['id']).get('ports')

        # Clear these interfaces from this router
        body = {}
        for port in ports:
            body['port_id'] = port['id']
            client.remove_interface_router(router['id'], body)

        # And then delete this router
        client.delete_router(router['id'])
        LOG.warn("Delete router: %s" % router['id'])


@wrap_exception(exc_type='delete')
def delete_fip(fip_id, region_name=None):
    client = get_neutronclient(region_name)
    update_dict = {'port_id': None}
    client.update_floatingip(fip_id,
                             {'floatingip': update_dict})
    client.delete_floatingip(fip_id)


@wrap_exception(exc_type='stop')
def stop_fip(fip_id, region_name=None):
    client = get_neutronclient(region_name)

    try:
        fip = client.show_floatingip(fip_id).get('floatingip')
    except NeutronClientException:
        fip = None

    if fip and fip['uos:registerno']:
        return True

    update_dict = {'port_id': None}
    client.update_floatingip(fip_id,
                             {'floatingip': update_dict})
    client.delete_floatingip(fip_id)
    return False


@wrap_exception(exc_type='delete')
def delete_router(router_id, region_name=None):
    client = get_neutronclient(region_name)

    router = client.show_router(router_id).get('router')

    # Delete VPNs of this router
    vpns = client.list_pptpconnections(router_id=router_id).get('pptpconnections')
    for vpn in vpns:
        client.delete_pptpconnection(vpn['id'])

    # Remove floatingips of this router
    project_id = router['tenant_id']
    fips = client.list_floatingips(tenant_id=project_id).get('floatingips')
    update_dict = {'port_id': None}
    for fip in fips:
        client.update_floatingip(fip['id'],
                                 {'floatingip': update_dict})

    # Remove subnets of this router
    ports = client.list_ports(device_id=router_id).get('ports')
    for port in ports:
        body = {}
        if port['device_owner'] == 'network:router_interface':
            body['subnet_id'] = port['fixed_ips'][0]['subnet_id']
            client.remove_interface_router(router_id, body)

    time.sleep(5)
    # And then delete this router
    client.delete_router(router_id)


@wrap_exception(exc_type='stop')
def stop_router(router_id, region_name=None):
    return True


@wrap_exception(exc_type='list')
def listener_list(project_id, region_name=None, project_name=None):
    client = get_neutronclient(region_name)
    if project_id:
        listeners = client.list_listeners(tenant_id=project_id).get('listeners')
    else:
        listeners = client.list_listeners().get('listeners')

    formatted_listeners = []
    for listener in listeners:
        status = utils.transform_status(listener['status'])
        admin_state = const.STATE_RUNNING if listener['admin_state_up'] else const.STATE_STOPPED
        created_at = utils.format_datetime(listener.get('created_at', timeutils.strtime()))
        formatted_listeners.append(Listener(id=listener['id'],
                                            name=listener['name'],
                                            admin_state_up=listener['admin_state_up'],
                                            admin_state=admin_state,
                                            connection_limit=listener['connection_limit'],
                                            project_id=listener['tenant_id'],
                                            project_name=project_name,
                                            resource_type=const.RESOURCE_LISTENER,
                                            status=status,
                                            original_status=listener['status'],
                                            created_at=created_at))
    return formatted_listeners


@wrap_exception(exc_type='bulk')
def delete_listeners(project_id, region_name=None):
    client = get_neutronclient(region_name)
    listeners = client.list_listeners(tenant_id=project_id).get('listeners')
    for listener in listeners:
        client.delete_listener(listener['id'])


@wrap_exception(exc_type='get')
def listener_get(listener_id, region_name=None):
    try:
        listener = get_neutronclient(region_name).show_listener(listener_id).get('listener')
    except NeutronClientException:
        return None

    status = utils.transform_status(listener['status'])
    return Listener(id=listener['id'],
                    name=listener['name'],
                    resource_type=const.RESOURCE_LISTENER,
                    status=status,
                    original_status=listener['status'])


@wrap_exception(exc_type='stop')
def stop_listener(listener_id, region_name=None):
    client = get_neutronclient(region_name)
    update_dict = {'admin_state_up': False}
    client.update_listener(listener_id, {'listener': update_dict})


@wrap_exception(exc_type='delete')
def delete_listener(listener_id, region_name=None):
    client = get_neutronclient(region_name)
    client.delete_listener(listener_id)


@wrap_exception(exc_type='put')
def quota_update(project_id, user_id=None, region_name=None, **kwargs):
    """
    kwargs = {"floatingip": 10,
              "network": 20,
              "router": 1024,
              ...}
    """
    client = get_neutronclient(region_name)
    body = {
        "quota": kwargs
    }
    client.update_quota(project_id, body=body)
