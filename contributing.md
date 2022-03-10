So excited that you're thinking of contributing!!

First, you can probably find things to work on in the issues section of the
[GitHub page](https://github.com/eBay/goose/issues).

Once you've found something you want to do, you can clone the repository and
ensure that the tests work. There's a `Makefile` at the repository root which
should have a bunch of useful commands.

You need to have python3 installed.

You can run the tests by running `make tests`.

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
