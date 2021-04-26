* *setup.py*: Move this function to an independent module
* *sink_connector.py*, *web_monitor_agent.py*: **URGENT!** Run next call under `daemon.DaemonContext()` context, following specifications [PEP 3143](https://www.python.org/dev/peps/pep-3143/)
* *src/communication_manager.py*: Keep a permanent track of processed messages, therefore `auto_offset_reset` can be set to `"latest"` without potential duplication
* *src/communication_manager.py*: Validate that this values are optimal (Load test required for a better tuning)
* *src/config.py*: Use a more secure storage for secrets (e.g. [Hashicorp Vault](https://www.vaultproject.io/)), actual security is a read-only access for file-owner on *.env*
* *src/config.py*: Encrypt password after using them (accessing them with a method), therefore they have less chance to ppear clear-text, e.g. with system dump
* *src/store_manager.py*: Create a tuning setup/config file for the values bellow
* *src/store_manager.py*: Implement a more accurate status control, see psycopg2 docs, [Connection status constants](https://www.psycopg.org/docs/extensions.html#connection-status-constants)
* *src/store_manager.py*: Analyze the viability of substituting [io.StringIO()](https://docs.python.org/3/library/io.html#io.StringIO) by [mmap.mmap()](https://docs.python.org/3/library/mmap.html#mmap.mmap)
* *src/store_manager.py*: **URGENT!** Substitute metric_dict.values() by specific calls to the keys, for ensuring the right field's order
* *\<ALL\>*: Fix our docstrings, therefore [Sphinx](https://www.sphinx-doc.org/en/master/) + [Napoleon](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/index.html), can generate the appropiated HTML documentation
* *\<ALL\>*: Control in CI between the status of remote repo (which files are not safe to store in Git) and local (Which files require read-only access)
* *src/communication_manager.py*: **URGENT!** Enabling group_id!=None goes in unexpected scenarion where messages are not cosumed. Investigate further
