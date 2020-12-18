# RecipeRadar API

The RecipeRadar API provides data services to the RecipeRadar [frontend](https://www.github.com/openculinary/frontend) application.

It provides endpoints to support the following functionality:

* Recipe and ingredient search
* User feedback collection

The API has high uptime and availability requirements since it's a core part of the [frontend](https://www.github.com/openculinary/frontend) recipe search experience.

## Install dependencies

Make sure to follow the RecipeRadar [infrastructure](https://www.github.com/openculinary/infrastructure) setup to ensure all cluster dependencies are available in your environment.

## Development

To install development tools and run linting and tests locally, execute the following commands:

```sh
$ make lint tests
```

## Local Deployment

To deploy the service to the local infrastructure environment, execute the following commands:

```sh
$ make
$ make deploy
```
