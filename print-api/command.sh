#!/usr/bin/bash

curl -XPOST localhost:8000/print_task -H 'Content-Type: application/json' -d '{"task_name":"LEETCODE ARRAYBUFFER", "task_description":"Complete 33. Counting Bits Leetcode problem", "priority":"HIGH"}'
