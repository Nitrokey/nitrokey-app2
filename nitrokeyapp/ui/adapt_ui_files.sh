#!/bin/bash

cp bak.org/resources.qrc .
cp -r bak.org/*.ui .


sed -i -e 's@../../resources.qrc@resources.qrc@g' *.ui

#sed -i -e 's@<file>images/@<file>images/@g' resources.qrc
