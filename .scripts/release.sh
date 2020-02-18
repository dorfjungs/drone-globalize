#!/bin/bash
VERSION=$1
V_MAJOR=$(echo $VERSION | cut -d. -f1)
V_MINOR=$(echo $VERSION | cut -d. -f2)
V_PATCH=$(echo $VERSION | cut -d. -f3)

TAGS=( "v${V_MAJOR}" "v${V_MAJOR}.${V_MINOR}" "v${V_MAJOR}.${V_MINOR}.${V_PATCH}" )

echo -n "The following tags will be published: "

for tag in "${TAGS[@]}"; do
  echo -n "$tag";
  echo -n " "
done

echo ""

while true; do
  read -p "Continue? (y/n)" yn

  case $yn in
      [Yy]* )
        for tag in "${TAGS[@]}"; do
          git tag -fa $tag -m "Version $tag"
          git push -f origin $tag
        done
        break;;
      [Nn]* ) exit;;
      * ) echo "Please answer yes or no.";;
  esac
done
