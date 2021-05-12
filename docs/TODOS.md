* *initialize_infra.py*: Move this function to an independent module
* *sink_connector.py*, *web_monitor_agent.py*: **URGENT!** Run next call under `daemon.DaemonContext()` context, following specifications [PEP 3143](https://www.python.org/dev/peps/pep-3143/)
* *src/communication_manager.py*: Keep a permanent track of processed messages so that `auto_offset_reset` can be set to `"latest"` without potential duplication
* *src/communication_manager.py*: Validate that this values are optimal (load test required for better tuning)
* *src/config.py*: Use a more secure storage for secrets (e.g. [Hashicorp Vault](https://www.vaultproject.io/)), currently security is implemented as read-only access for file-owner on *.env*
* *src/config.py*: Encrypt passwords after using them (accessing them with a method) so that they have less chance to appear clear-text, e.g. with system dump
* *src/store_manager.py*: Create a tuning setup/config file for the values below
* *src/store_manager.py*: Implement a more accurate status control, see psycopg2 docs, [Connection status constants](https://www.psycopg.org/docs/extensions.html#connection-status-constants)
* *src/store_manager.py*: Analyze the viability of substituting [io.StringIO()](https://docs.python.org/3/library/io.html#io.StringIO) with [mmap.mmap()](https://docs.python.org/3/library/mmap.html#mmap.mmap)
* *src/store_manager.py*: **URGENT!** Substitute metric_dict.values() with specific calls to the keys, for ensuring the right order of the fields
* *\<ALL\>*: Fix our docstrings so that [Sphinx](https://www.sphinx-doc.org/en/master/) + [Napoleon](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/index.html) can generate the appropriate HTML documentation
* *\<ALL\>*: Control in CI between the status of remote repo (which files are not safe to store in Git) and local (which files require read-only access)
* *src/communication_manager.py*: **URGENT!** Enabling group_id!=None goes in unexpected scenario where messages are not consumed. Investigate further
