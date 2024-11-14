4.0.2 - Released on 2024-11-14
------------------------------
* Authorize older zipkin and prometheus library.

4.0.1 - Released on 2024-11-03
------------------------------
* Binding for blacksmith 4.
* Drop support of python 3.8
* Use uv / pdm instead of poetry
* Replace black, flake8 and isort by ruff
* Update the CI

3.3.0 - Released on 2024-10-10
------------------------------
* Add support of the Nomad Service discovery

3.2.0 - Released on 2024-10-10
------------------------------
* Fix the __version__ property

3.0.1 - Released on 2024-10-10
------------------------------
* Update deps

2.2.0 - Released on 2024-04-19
------------------------------
* Release an alpha middleware for zipkin based on zk
  Stay undocumented until it has been tested on prod
* Update deps

2.1.0 - Released on 2023-12-01
------------------------------
* Add a middleware to inject a header statically from the conf

2.0.2 - Released on 2022-10-12
------------------------------
* Fix the error_parser implementation1

2.0.1 - Released on 2022-10-11
------------------------------
* Update to blacksmith 2.0

2.0.0 - Released on 2022-10-11
------------------------------
* Broken release :/

1.0.2 - Released on 2022-10-07
------------------------------
* Readd previews dependency prometheus_client, always required
* Improve developper experience while writing tests due to prometheus_client
* Update the documentation

1.0.1 - Released on 2022-10-07
------------------------------
* Update dependencies
  * remove prometheus_client from the dependencies, only dev deps
* Update to be compatible with Pyramid >1.10

1.0.0 - Released on 2022-02-12
------------------------------
* Update to blacksmith 1.0
* Rename config "timeout" to "read_timeout"

0.3.0 - Released on 2022-01-19
-------------------------------
* Add client middlewares for authentication purpose
* Add typing support (best effort since pyramid is not typed)

0.2.0 - Released on 2022-01-13
------------------------------
* Add middlewares
  - prometheus
  - circuitbreaker
  - httpcaching
* Let users add their own middlewares

0.1.0 - Released on 2022-01-08
------------------------------
* Initial Release
