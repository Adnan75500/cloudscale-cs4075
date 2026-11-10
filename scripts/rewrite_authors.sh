#!/bin/bash
set -e

export FILTER_BRANCH_SQUELCH_WARNING=1

git filter-branch -f --env-filter '
case "$GIT_COMMIT" in
  611a677cb325e2aeb75145b8aa0a89626fdc56e0|\
  61dd71ceadf692f83c1770ab08f71fa3da5775c1|\
  e9b503a9d7f33764b8314801027fe3f41e9bee7e|\
  233adcefc116a775a0c07e2ebfd005047442e76e|\
  8d827312f8c09a9a4d06478da85f43f8e982599a|\
  59566dc0fc906231f5471f875bd503086c295e17)
    export GIT_AUTHOR_NAME="HUZAIFA23901"
    export GIT_AUTHOR_EMAIL="huzaifa.auaccess1719@gmail.com"
    export GIT_COMMITTER_NAME="HUZAIFA23901"
    export GIT_COMMITTER_EMAIL="huzaifa.auaccess1719@gmail.com"
    ;;
esac
' HEAD

