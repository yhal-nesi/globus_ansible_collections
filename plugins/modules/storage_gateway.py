import globus_sdk

from ansible.module_utils.basic import AnsibleModule

import ansible_collections.nesi.globus.plugins.module_utils.gcs_util as gcs_util # type: ignore
from ansible_collections.nesi.globus.plugins.module_utils.gcs_util import Action # type: ignore

def storage_gateway_spec():
    return dict(
        admin_managed_credentials = dict(type='bool',
                                        required=False),
        allowed_domains = dict(type='list', required = False),
        authentication_timeout_mins = dict(type='int', 
                                        required = False),
        connector_id = dict(type = gcs_util.get_connector_id,
                            required=False),
        display_name = dict(type='str', required=False),
        high_assurance = dict(type='bool', required=False),
        identity_mappings = dict(type='list', required=False),
        load_dsi_module = dict(type='string', required=False),
        policies = dict(type='dict', required=False),
        process_user = dict(type='string', required=False),
        require_mfa = dict(type='bool', required=False),
        restrict_paths = dict(type='dict', required=False),
        users_allow = dict(type='list', required=False),
        users_deny = dict(type='list', required=False)
    )

def main():
    try:
        spec = gcs_util.common_spec() | storage_gateway_spec()
        module = AnsibleModule(argument_spec= spec,
                                    supports_check_mode=True)
        gcs_client = gcs_util.create_gcs_client(module)

        id = module.params["id"]
        if (id is None):
            actual = None
        else:
            actual = get_storage_gateway_data(gcs_client, id)

        state = module.params["state"]
        if state == "absent":
            desired = None
        else:
            desired = gcs_util.read_keys(
                storage_gateway_spec().keys(), 
                module
                )

        def nothing():
            module.exit_json(changed = False, data = actual)
        
        def delete():
            gcs_client.delete_storage_gateway(id)
            module.exit_json(changed = True, data = {"id": id})

        def create():
            desired["DATA_TYPE"] = "storage_gateway#1.2.0"
            data = gcs_client.create_storage_gateway(desired).data
            module.exit_json(changed = True, data = data)

        def update():
            desired["DATA_TYPE"] = "storage_gateway#1.2.0"
            gcs_client.update_storage_gateway(id, 
                                              data = desired)
            data = get_storage_gateway_data(gcs_client, id)
            module.exit_json(changed = True, data = data)

        action_table = {Action.NOTHING: nothing,
                        Action.DELETE:  delete,
                        Action.UPDATE:  update,
                        Action.CREATE:  create}      
        
        action_table[gcs_util.plan(desired, actual)]()

    except globus_sdk.GlobusError as e:
        module.fail_json(msg = str(e))

@gcs_util.none_if_not_found
def get_storage_gateway_data(gcs_client, id):
    return gcs_client.get_storage_gateway(
        storage_gateway_id = id,
        include = "private_policies"    
    ).data

if __name__ == '__main__':
    main()
