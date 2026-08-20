The log analyzer is separated into two sections: code that is intended to for use by everyone, and code that only
makes sense for opus.
The former is in the top-level directory, while the latter is in the sub-directory `opus/`.
Other users of this code should create their own subdirectory for their project-specific code.

The log analyzer accesses the opus-specific code via a **configuration**.
It looks for a class called `Configuration` in the file `opus/Configuration.py`.
You can tell the log analyzer to look for the `Configuration` class in a different file by specifying the
name of the file in which to find it.
Because Python expects the name of a "module", you would write:
```
log_analyzer --configuration myproject.Configuration
```
to tell it find your configuration in `myproject/Configuration.py`.

## Configuration

Your configuration should typically be a subclass of `AbstractConfiguration`.
This is not enforced, but your configuration class should certainly implement at least the same required methods 
that an `AbstractConfiguration` implements.

The most important method implemented by a configuration is 

```
create_session_info(self, uses_html: bool) -> AbstractSessionInfo
```
This method takes a single flag, indicating whether the user can handle an html result.  (See Markup below.) 
It returns a `SessionInfo`, which is an object that parses the log entries of a single user's session.

```
additional_template_info(self) -> Dict[str, Any]
```
Certain fixed but configuration specific information must be given to the output-generating template for it to 
generate its output. 
For opus, this is the name of the flags, and the base URL.  You are free to pass this or other information.

```
def show_summary(self, sessions: List[Session], output: TextIO) -> None
```
This program is designed to show detailed information about the logs.
However you can also ask for a summary.  We do not know what your summary should look like.
The precise format of a `Session` can be found in the code, but in general it contains the IP of the user, the
time that the session started, the list of log entries of that user, and the SessionInfo that was generated.


## Session Info

When the log analyzer realizes that a new session has started, it calls `create_session_info()` above to create a
new SessionInfo object.
This SessionInfo object is expected to be a subclass of `AbstractSessionInfo`, but this is
not enforced.

The session info's method:
```
parse_log_entry(self, entry: LogEntry) ->  Tuple[List[str], Optional[str]]
```
is called repeatedly for each log entry that is part of this session.  
Once the session has ended, the method
```
def get_session_flags(self) -> IconFlags
```
is called once, both to get the list of actions performed by this session, and to mark that the session is complete.


The method ```parse_log_entry()``` is the most complicated.
Its job is to take a log entry and figure out what it means.
It keeps track of whatever state it needs so that it can parse log entries in the context of previous log entries. 
Its return value is a two-element tuple.
* The first element of the tuple is a sequence of zero or more strings.
These strings should indicate the action(s) that have been performed by the URL.
If this sequence is empty, then this log entry is ignored, and no output is generated for it.
* The second element of the tuple is either `None`, or a string giving a relative URL.
Clicking on this URL should show the person running the log analyzer roughly the same as what the user saw.

If `create_session_info()` is passed `False` for `uses_html`, then the strings returned as the first element of the
tuple should be normal strings.  If the argument is `True`, then the strings can either be normal strings or the
special subclass of string called `Markup`. 

### Markup
A Markup string is a string that has been declared safe to insert into an HTML file.
Passing an object to the `Markup` constructor converts it to text, and wraps it up in such a way to mark it
safe without escaping. 
To escape the text, use the `Markup.escape()` method instead.
```
    >>> Markup('Hello, <em>World</em>!')
    Markup('Hello, <em>World</em>!')
    >>> Markup(42)
    Markup('42')
    >>> Markup.escape('Hello, <em>World</em>!')
    Markup('Hello &lt;em&gt;World&lt;/em&gt;!')
```

The class `AbstractSessionInfo` also includes a convenience methods to help you work with Markup.
The static method `safe_format()` is a `Markup` version of `format`.  It takes a format argument followed by one
or more arguments.  The format argument must be properly html.
If any of the arguments are `Markup` strings, they are directly interpolated into the format argument.
Any argument that isn't a `Markup` string is html-quoted as necessary before interpolation.

## The Template




 

