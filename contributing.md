So excited that you're thinking of contributing!!

First, you can probably find things to work on in the issues section of the
[GitHub page](https://github.com/eBay/goose/issues).

Once you've found something you want to do, you can clone the repository and
ensure that the tests work. There's a `Makefile` at the repository root which
should have a bunch of useful commands.

You need to have python3 installed.

You can run the tests by running `make tests`. There are various linters there
which will be required for your PR to eventually pass the build.

To get a server up and running, you'll need to get GitHub credentials with the
"repo" scope, which you should be able to get from the [personal access token
page](https://github.com/settings/tokens). The server expects `GITHUB_USERNAME`
to be the username and `GITHUB_PASSWORD` to be the token that you generated.

From there, you should be able to get a server running with `make web`.

That server won't be terribly interesting without a config file. To specify one,
you can set the `GOOSE_CONFIG` variable to where it can find the config in your
filesystem.

When you're ready to push your code, send out a pull request. If you need early
feedback, feel free to make a draft PR and we'll help where we can.

To start a local server, you can put a Dockerfile in your goose setup and run it
like you would other docker files.

```
mkdir ~/projects/goose-internal  # The directory isn't important. Just for demo purposes.
cd ~/projects/goose-internal
# create the Dockerfile from the readme & a config file
docker build -t goose-internal . # Build the docker image. goose-internal is the image's local name
docker run goose-internal        # run the image we just built.
```

From there, you can send it git events to validate your implementation. There
are some already in the `./goose/fixtures` directory, or you can see the output
of any of your configured git hooks in the settings of your git repository. The
`drive-local-message.sh` will help you replay them. Given that receive git hooks
need to be accessible from your github instance, the you'll probably need to
deploy this docker setup before live testing can be done. Those instructions are
out of scope for this README, but your hosting provider probably has useful
information.
