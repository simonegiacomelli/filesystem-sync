# Filesystem-sync

This is a small library to monitor a filesystem and propagate changes to another filesystem to keep them in sync.


The source and target filesystems are assumed to be on different machines and there is a small part that serializes the filesystem changes to be sent over the transport (e.g., network)

The source filesystem is monitored using [watchdog](https://pypi.org/project/watchdog/).

There are in essence two parts: 
- one part to debounce the filesystem events to avoid frenzied activity
- one part that takes in the debounced events and propagates them to the target filesystem

Both parts have tests and are tested in isolation.

## Debounce
This is a general implementation that keeps a buffer and notifies the observer when a timeout is reached.

## Sync


### Sync-source
This part has the following input:
- a reference to the root of the monitored source filesystem
- a list of filesystem change events


The output is:
- a list of filesystem changes that can be serialized.
- such list can be an aggregated list of changes (e.g., a file was created and then modified, the two events can be aggregated into a single event)

### Sync-target
This part has the following input:
- a reference to the root of the target filesystem
- a list of filesystem aggregated change events

The output is:
- the target filesystem is updated to reflect the changes


### Sync-init
This part has the following input:
- a reference to the root of the monitored source filesystem

The output is:
- a list of filesystem aggregated change events that reflect the current state of the source filesystem
