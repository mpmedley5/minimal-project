import werkzeug
print('werkzeug module', werkzeug)
print('version attr', getattr(werkzeug, '__version__', None))
print('file', werkzeug.__file__)
