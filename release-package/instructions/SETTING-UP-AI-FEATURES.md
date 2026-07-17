# Setting up AI content generation (optional)

Project Tracker's "Generate content" and "Distill voice profile" features
use Anthropic's Claude AI. This is **optional** — everything else in the
app works without it, and until you add a key, you'll just see a message
telling you it's not set up yet instead of anything breaking.

There's a cost to using this: Anthropic charges per use, based on your own
account. Project Tracker does not add any markup or subscription on top —
you pay Anthropic directly, only for what you generate.

## Step 1 — Get an API key

1. Go to **console.anthropic.com** and create an account if you don't have
   one.
2. Add a small amount of credit (a few dollars covers a lot of generation —
   each request is typically a fraction of a cent to a few cents).
3. Go to **API Keys** and create a new key. It'll look like
   `sk-ant-...` — copy the whole thing.

Keep this key private — anyone with it can use your Anthropic credit.

## Step 2 — Add it to Project Tracker

1. Open Project Tracker and click **⚙️ Settings** in the left sidebar (or
   the top menu).
2. Under **AI content generation**, paste your key into the **Anthropic
   API key** field.
3. Click **Save settings**.

That's it — no restart needed, no files to edit. "Generate content" and
"Distill from sources" will now work straight away.

Your key is stored locally in your own database, on your own computer —
it's never sent anywhere except directly to Anthropic when you choose to
generate something.

## Troubleshooting

- **Still says no key configured?** Go back to Settings and confirm it
  saved — you should see "A key is currently set" under the field.
- **Want to change the AI model used?** There's an optional "Model" field
  right below the API key in Settings — leave it blank to use the default.
- **Something else generation-related looks wrong?** Check the message
  shown on screen first — Project Tracker is built to show the actual
  error rather than fail silently.
