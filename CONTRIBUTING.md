# Contributing

If you want to participate in this project, please follow this guidline.

Fork and clone this repository:

```bash
git clone git@github.com:your-username/osmapi.git
```

Install the dependencies using `pip`:

```bash
pip install -r requirements.txt
pip install -r test-requirements.txt
```

Make sure the tests pass:

```bash
nosetests --verbose
```

You can even run the tests on different versions of Python with `tox`:

```bash
tox
```

To ensure a good quality of the code use `flake8` to check the code style:

```bash
flake8 --install-hook
```

To create a pull request make sure

1. You choose the `develop` branch as a target for new/changed functionality, `master` should only be targeted for urgent bugfixes.
2. While it's not strictly required, it's highly recommended to create a new branch in your branch for each pull request.
3. Push to your fork and [submit a pull request][pr].
4. Check if the [build ran successfully][ci] and try to improve your code if not.

At this point you're waiting for my review.
I might suggest some changes or improvements or alternatives.

Some things that will increase the chance that your pull request is accepted:

* Write tests.
* Follow the Python style guide ([PEP-8][pep8]).
* Write a [good commit message][commit].

[ci]: https://travis-ci.org/metaodi/osmapi
[pr]: https://github.com/metaodi/osmapi/compare/
[pep8]: https://www.python.org/dev/peps/pep-0008/
[style]: https://github.com/thoughtbot/guides/tree/master/style
[commit]: http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
