# Centrice
Mirror Domain Distribution Central Service


## API

<pre>
1.  Fetch accessible domains in the default public rank
      GET /domains/fetch_public?site=$site_id
        Params:
          site: The site id, required

      For example: /domains/fetch_public?site=cdt

      Output:
        Domain list seperated by line feed char

2.  Fetch domains by rank and status
      GET /domains/fetch?site=$site_id&rank=0&status=up
        Params:
          site: The site id, required
          rank: The domain rank, default is 0, i.e. public.
          status: The accessible status, default is up,i.e. not blocked.
                  Enum(up|down)
      Output:
        Domain list seperated by line feed char

3.  Update site domains
      POST /domains/update
      Body: site=$site_id&status=up&domains=a.example.com,b.example.com
        Params:
          site, status: Same as `fetch` API
          domains: Domains seperated by comma
      Output:
        200 status code indicate success, otherwise error occurs.
</pre>

### Installation
Clone this repository.
```bash
cd src;
pip install -r requirements.txt;
touch  settings_local.py;
python app.py;
```
