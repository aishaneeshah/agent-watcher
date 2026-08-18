current:
  statement: ""         # What you're trying to accomplish this session
  mode: implement       # brainstorm | implement | debug | analyze | review
  scope: []             # Areas/modules/concerns in scope (empty = no restriction)
  non_goals: []         # Explicitly out-of-scope items (watcher will flag these)
  authorized_by: user
  session_id: ""        # Auto-filled by /goal-set
  updated_at: ""        # Auto-filled by /goal-set

history: []
# Previous goal versions are appended here automatically by /goal-set.
# Format:
# history:
#   - v1:
#       statement: "..."
#       mode: brainstorm
#       authorized_by: user
#       session_id: "..."
#       reason: "updated by user"
#       updated_at: "..."
