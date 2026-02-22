test:
	python3 -m unittest discover -s tests -q

package:
	python3 scripts/package_release.py --out dist/afl.zip
