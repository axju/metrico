=======
metrico
=======
This is in development! Just a kind of beta version!

Just some metrics for social networks or basically any platform where users post content, write comments and following each other.

You can uses this project as a python package and write your own scrips. See the example folder. But it has also a nice cli. A tui will coming soon, I guess.

Install
-------
It is easy to install in a python environment::

    pip install metrico[full]

This will install all dependency. To make it cleaner, you can install only the dependency you need. If you only need the core::

    pip install metrico

The cli required "rich", 'pip install rich' or::

    pip install metrico[cli]

To get some data you need the api package like "pip install python-youtube", "pip install python-tiktok" or::

    pip install metrico[youtube]
    pip install metrico[tiktok]

or install all of them with::

    pip install metrico[hunters]


Config
------
Now you need a configuration. Like the database or the API keys. Load the config from a toml file::

    from metrico.core import MetricoCore

    metrico = MetricoCore(filename="my_config.toml")

or load the default config files::

    metrico = MetricoCore.default()

This will load all available config files in the following order:
  1. /etc/metrico/config.toml
  2. ~/config/metrico/config.toml
  3. metrico.toml mext to your script
  4. ./metrico.toml
  5. file from environment variable METRICO_CONF

You can also hack the config object in your script::

    from metrico.core import MetricoConfig, MetricoCore
    from metrico.core.utils import BasicClassConfig

    # create metrico config object and set the database and youtube api key
    config = MetricoConfig()
    config.db.url = f"sqlite://"
    config.hunters["youtube"] = BasicClassConfig(config={"key": "AIzaSyDXnm6hi..."})

    # create metrico object with locale config
    metrico = MetricoCore(config=config)

Examples
--------
Take a look in the example folder. There are some simple one.

The cli
-------
Some commands::

    metrico tools conf
    metrico tools stats
    metrico tools migrate
    metrico tools makemigrations

    metrico account --help
    metrico account 1 {info|rel|update|...}
    metrico account 1 rel {info|stats|comment|...}

    metrico accounts --help
    metrico accounts {some filter, limit, etc.} {list|update|count}

    metrico media --help
    metrico media 1 {info|rel|update|...}
    metrico media 1 rel {info|stats|comment|...}

    metrico medias --help
    metrico medias {some filter, limit, etc.} {list|update}


Postgres
--------
Run local PostgresSQL with docker::

    docker run --name postgres-metrico -e POSTGRES_USER=metrico -e POSTGRES_PASSWORD=1234 -p 5432:5432 -d postgres

    docker run --name metrico-de0x01 -e POSTGRES_USER=metrico -e POSTGRES_PASSWORD=1234 -p 5432:5432 -d postgres

Show container::

    docker ps -a

Stop and delete container::

    docker stop postgres-metrico
    docker rm postgres-metrico
