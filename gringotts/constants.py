# Order and resource State
STATE_RUNNING = 'running'
STATE_STOPPED = 'stopped'
STATE_STOPPED_IN_30_DAYS = 'stopped_in_30_days'
STATE_DELETED = 'deleted'
STATE_SUSPEND = 'suspend'
STATE_CHANGING = 'changing'
STATE_ERROR = 'error'


# Service type
SERVICE_COMPUTE = 'compute'
SERVICE_BLOCKSTORAGE = 'block_storage'
SERVICE_NETWORK = 'network'
SERVICE_MONITOR = 'monitor'


# Resource type
RESOURCE_INSTANCE = 'instance'
RESOURCE_IMAGE = 'image'
RESOURCE_SNAPSHOT = 'snapshot'
RESOURCE_VOLUME = 'volume'
RESOURCE_FLOATINGIP = 'floatingip'
RESOURCE_ROUTER = 'router'
RESOURCE_ALARM = 'alarm'


# Product Name
PRODUCT_INSTANCE_TYPE_PREFIX = 'instance'
PRODUCT_VOLUME_SIZE = 'volume.size'
PRODUCT_SNAPSHOT_SIZE = 'snapshot.size'
PRODUCT_SATA_VOLUME_SIZE = 'sata.volume.size'
PRODUCT_FLOATINGIP = 'ip.floating'
PRODUCT_ROUTER = 'router'
PRODUCT_ALARM = 'alarm'


# Bill status
BILL_PAYED = 'payed'
BILL_OWED = 'owed'
