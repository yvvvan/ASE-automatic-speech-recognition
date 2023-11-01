# ASE-Gruppe-4 

## Table of Contents
0. [GIT Command](#git-Command)
1. [Aufgabe 1: Merkmalsextraktion I](#aufgabe-1)

## GIT Command
``` bash
## STAGE & SNAPSHOT
# add a file as it looks now to your next commit (stage)
git add [file]

# unstage a file while retaining the changes in working directory
git reset [file]

# commit your staged content as a new commit snapshot
git commit -m “[descriptive message]”


## SHARE & UPDATE
# fetch and merge any commits from the tracking remote branch
git pull

# Transmit local branch commits to the remote repository branch
git push 


## REWRITE HISTORY
# clear staging area, rewrite working tree from specified commit
git reset --hard [commit id]


## TEMPORARY COMMITS
# Save modified and staged changes
git stash

# write working from top of stash stack
git stash pop

# discard the changes from top of stash stack
git stash drop


## BRANCH & MERGE
# list your branches. a * will appear next to the currently active branch
git branch

# create a new branch at the current commit
git branch [branch-name]

# switch to another branch and check it out into your working directory
git checkout
git checkout [branch-name]

```

## Aufgabe 1
**Merkmalsextraktion I (Fensterung)**
![Dastellung Frames](data/images/aufgabe1.png)
Figure 1: Dastellung der ersten vier Frames (mit Multiplikation mit einem
Hamming-Fenster) für TEST-MAN-AH-3O33951A.wav