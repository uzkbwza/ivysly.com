#!/bin/sh

function replace_footnotes() {
  # replace footnotes of posts with html footnote links
  filename=$1
  sed -i -E "s|(\[)([0-9]+)(\*\])|<a href=\"#fn\2\" id=\"ref\2\"><sup>[\2]</sup></a>|g; \
             s|(\[\*)([0-9]+)(\])|<a href=\"#ref\2\" id=\"fn\2\"><sup>[\2]</sup></a>|g" \
         $filename
}

rsync -av posts/* pelican/content/ --delete

for file in ls pelican/content/*.md
do
  replace_footnotes $file
done

echo "running footnotes script"
echo "generating blog"
cd pelican && make publish
cd ..
echo "removing existing blog contents" 
rm -r blog/*
echo "removing duplicates from pelican content folder (these already exist in the post folder)"
rm -r pelican/content/*
echo "copying pelican output contents to blog folder"
cp -r pelican/output/* blog

