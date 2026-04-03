.PHONY: setup deploy run

# Deploy all DAB resources and kick off the setup job.
# Override catalog/schema for shared workspaces:
#   make setup catalog=main schema=zscaler_alice
setup: deploy run

deploy:
	databricks bundle deploy \
		$(if $(catalog),--var catalog=$(catalog),) \
		$(if $(schema),--var schema=$(schema),)

run:
	databricks bundle run zscaler_setup \
		$(if $(catalog),--var catalog=$(catalog),) \
		$(if $(schema),--var schema=$(schema),)
