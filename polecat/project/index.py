from .handler import Handler

index_html = '''<!DOCTYPE html>
<html>
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta charset="UTF-8">
    <title>{default_title}</title>
  </head>
  <body>
    <div id="mount"></div>
    <script type="text/javascript">
      window.publicPath = 'https://s3-{region}.amazonaws.com/{bucket}/projects/{project}/bundle/{bundle_version}/'
    </script>
    <script
      type="text/javascript"
      src="https://s3-{region}.amazonaws.com/{bucket}/projects/{project}/bundle/{bundle_version}/{bundle}"
    >
    </script>
  </body>
</html>
'''


def get_index_html(bucket, project, bundle_version, region='ap-southeast-2',
                   bundle='index.js.gz', default_title=''):
    return index_html.format(
        bucket=bucket,
        project=project,
        bundle_version=bundle_version,
        region=region,
        bundle=bundle,
        default_title=default_title
    )


class IndexHandler(Handler):
    def prepare(self):
        self.index_html = self.project.get_index_html()

    def match(self, event):
        # TODO: Use regex
        return event.is_http() and \
           event.request.method == 'GET' or \
           event.request.path == '/'

    async def handle_event(self, event):
        return (self.index_html, 200, 'text/html')
