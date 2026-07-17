# assets/management/commands/seed_examples.py
"""Seeds generic example content so you can see what each part of the app
looks like before adding your own real data: six ready-to-use
PromptTemplates, two sample Assets, a pre-filled VoiceProfile (as if it had
already been distilled), one finished GenerationJob with a fake generated
blog post (so the whole flow — asset in, page out — is visible end to end),
and two example Products with funnel steps and sale history so Products
isn't empty either.

Everything created here is prefixed "[Example]" so it's easy to spot and
remove later. Safe to re-run: uses get_or_create, won't duplicate.

Usage:
    python manage.py seed_examples            # create the example content
    python manage.py seed_examples --remove    # delete it again
"""
import datetime

from django.core.management.base import BaseCommand

from assets.models import Asset, GenerationJob, PromptTemplate, VoiceProfile
from pages.models import Page
from products.models import FunnelStep, Product, Sale

PREFIX = "[Example]"

PROMPT_TEMPLATES = [
    {
        "name": f"{PREFIX} Blog post (long-form)",
        "content_type": "blog",
        "system_prompt": (
            "You are a marketing copywriter turning raw source material (transcripts, notes, "
            "past content) into a publish-ready blog post.\n\n"
            "Structure:\n"
            "- A hook opening (1-2 sentences) that states the core idea or problem\n"
            "- 3-5 short sections with clear subheadings\n"
            "- Concrete examples or specifics pulled from the source material — no generic filler\n"
            "- A short closing with a single clear next step or call to action\n\n"
            "Length: 500-800 words. Write in second person (\"you\") where natural. Avoid corporate "
            "jargon, avoid starting sentences with \"In today's world\" or \"In conclusion.\""
        ),
    },
    {
        "name": f"{PREFIX} Social media caption",
        "content_type": "social",
        "system_prompt": (
            "You are writing a short social media caption (Instagram/LinkedIn style) from the "
            "source material provided.\n\n"
            "Rules:\n"
            "- Open with a scroll-stopping first line — a question, a bold claim, or a specific number\n"
            "- 3-6 short lines/paragraphs, heavy white space, no walls of text\n"
            "- End with one clear call to action (comment, DM, link in bio, etc.)\n"
            "- Include 3-5 relevant hashtags at the end, on their own line\n"
            "- No emojis unless the source material uses them"
        ),
    },
    {
        "name": f"{PREFIX} Nurture / marketing email",
        "content_type": "email",
        "system_prompt": (
            "You are writing a single marketing/nurture email from the source material provided.\n\n"
            "Structure:\n"
            "- Subject line (on its own line, prefixed \"Subject:\")\n"
            "- A personal, conversational opening line — not generic \"Hi [Name],\" filler\n"
            "- One clear idea per email — don't try to cover everything in the source material\n"
            "- A single call to action near the end, stated plainly\n"
            "- Sign-off in a warm, first-person voice\n\n"
            "Length: 150-300 words. Write like a real person emailing a friend about their "
            "business, not like a corporate newsletter."
        ),
    },
    {
        "name": f"{PREFIX} Funnel / sales page copy",
        "content_type": "funnel",
        "system_prompt": (
            "You are writing sales page / funnel copy for a digital product, using the source "
            "material as proof and detail (testimonials, results, features).\n\n"
            "Structure:\n"
            "- Headline: the specific outcome the product delivers, not a vague benefit\n"
            "- Subheadline: who it's for and why now\n"
            "- 3-5 bullet points on what's included, written as outcomes not features\n"
            "- A short \"why this, why me\" section using any credibility/proof from the source material\n"
            "- Pricing/offer framing with urgency only if it's genuinely true (no fake scarcity)\n"
            "- A closing call to action\n\n"
            "Tone: direct and confident, not hypey. Avoid superlatives (\"game-changing\", "
            "\"revolutionary\") unless the source material itself uses that language."
        ),
    },
    {
        "name": f"{PREFIX} Documentation / how-to guide",
        "content_type": "docs",
        "system_prompt": (
            "You are turning source material (notes, transcripts, rough instructions) into a "
            "clear how-to guide or piece of documentation.\n\n"
            "Structure:\n"
            "- A one-line summary of what this guide covers and who it's for\n"
            "- Numbered steps, one action per step\n"
            "- Call out any prerequisites or things to check before starting, up front\n"
            "- Note edge cases or common mistakes inline, not as a separate FAQ dump\n\n"
            "Tone: plain, precise, no marketing language. Assume the reader is capable but "
            "unfamiliar with this specific process."
        ),
    },
    {
        "name": f"{PREFIX} General repurposing (fallback)",
        "content_type": "general",
        "system_prompt": (
            "You are repurposing the source material into clear, well-organized written content "
            "based on any additional instructions provided. Match the tone and level of formality "
            "implied by the source material unless a voice profile or instructions say otherwise. "
            "Prefer concrete specifics over generic statements."
        ),
    },
]

ASSET_TESTIMONIAL = {
    "title": f"{PREFIX} Client testimonial transcript",
    "file_type": "text",
    "tags": "example, testimonial",
    "content": (
        "Interview snippet, recorded call, March 2026:\n\n"
        "\"Before working with [name], I was posting on Instagram maybe twice a month and "
        "honestly didn't really know what I was doing. Three months after we started, I had "
        "my first £1,200 launch week — from an audience of under 500 people. What actually "
        "changed wasn't the number of posts, it was that every post had a point. I stopped "
        "trying to sound like everyone else and started just... saying the thing. That's what "
        "people responded to.\"\n\n"
        "— early beta customer, described as \"a coach in her second year of business\""
    ),
}

ASSET_WRITING_SAMPLE = {
    "title": f"{PREFIX} Past blog post — writing sample",
    "file_type": "text",
    "tags": "example, writing-sample",
    "content": (
        "I used to think consistency meant posting every day. It doesn't. It means showing up "
        "with something worth reading, on a schedule you can actually keep.\n\n"
        "Most people quit content not because they run out of ideas, but because they set a "
        "pace that assumes infinite energy. Pick a rhythm you could keep up even on a bad week. "
        "That's the only kind of consistency that compounds."
    ),
}

VOICE_PROFILE = {
    "name": f"{PREFIX} Warm & Direct",
    "summary": (
        "Plainspoken and conversational. Favors short, punchy sentences over long explanations. "
        "Avoids hype language and prefers concrete specifics over generic claims."
    ),
    "tone_words": ["direct", "warm", "no-nonsense", "conversational", "grounded"],
    "sentence_length": "short",
    "words_to_avoid": [
        "game-changing", "revolutionary", "synergy", "leverage (as a verb)", "unlock your potential",
    ],
    "sample_paragraphs": [
        "I used to think consistency meant posting every day. It doesn't. It means showing up "
        "with something worth reading, on a schedule you can actually keep.",
        "What actually changed wasn't the number of posts, it was that every post had a point. "
        "I stopped trying to sound like everyone else and started just... saying the thing.",
    ],
    "do_notes": [
        "Use concrete numbers and specifics instead of vague claims",
        "Write in second person where natural",
        "Keep paragraphs short — 1-3 sentences",
    ],
    "dont_notes": [
        "Don't open with \"In today's world\" or similar throat-clearing",
        "Don't use more than one exclamation point per piece",
        "Don't pad with generic marketing language",
    ],
    "is_active": False,  # don't hijack the user's real default voice once they build one
}

EXAMPLE_GENERATED_BLOCKS = {
    "blocks": [
        {"type": "header", "data": {"text": "Why Consistency Beats Frequency", "level": 1}},
        {
            "type": "paragraph",
            "data": {
                "text": "Most people trying to build an audience think the fix is posting more. "
                "It isn't. The fix is picking a pace you can actually sustain — because the "
                "account that shows up every week for a year beats the one that shows up daily "
                "for a month and then goes quiet."
            },
        },
        {"type": "header", "data": {"text": "The pace you can't keep is worse than no plan at all", "level": 2}},
        {
            "type": "paragraph",
            "data": {
                "text": "One beta customer put it simply: she went from posting twice a month "
                "with no real plan to having her first £1,200 launch week, from an audience under "
                "500 people. What changed wasn't volume. It was that every post finally had a point."
            },
        },
        {"type": "header", "data": {"text": "What actually compounds", "level": 2}},
        {
            "type": "paragraph",
            "data": {
                "text": "Pick a rhythm you could keep up even on a bad week. Not your best week — "
                "your worst one. That's the only kind of consistency that compounds, because it's "
                "the only kind that survives contact with an actual life."
            },
        },
        {
            "type": "paragraph",
            "data": {
                "text": "If you're not sure where to start, look back at what you've already made — "
                "an old testimonial, a call transcript, a post that did well — and build from there "
                "instead of starting from a blank page every time."
            },
        },
    ]
}


PRODUCTS = [
    {
        "name": f"{PREFIX} 90-Day Content Sprint",
        "description": (
            "A guided 90-day program to build a consistent content habit — weekly prompts, "
            "templates, and accountability check-ins."
        ),
        "price": "147.00",
        "product_type": "course",
        "status": "active",
    },
    {
        "name": f"{PREFIX} Brand Voice Workbook",
        "description": (
            "A short workbook that walks you through defining your tone, sentence style, and "
            "words to avoid — the same questions this app's Voice Profile feature asks."
        ),
        "price": "27.00",
        "product_type": "digital_download",
        "status": "active",
    },
]

# (product index, contact, amount, days_ago) — spread across the last few weeks
# so the revenue rollup on the Products list looks like real activity, not one lump sum.
SALES = [
    (0, "147.00", 3),
    (0, "147.00", 11),
    (1, "27.00", 2),
    (1, "27.00", 9),
    (1, "27.00", 20),
]


class Command(BaseCommand):
    help = "Seed generic example prompt templates, assets, a voice profile and a sample generated page."

    def add_arguments(self, parser):
        parser.add_argument(
            "--remove", action="store_true", help="Delete all previously seeded example content instead."
        )

    def handle(self, *args, **options):
        if options["remove"]:
            self._remove()
            return

        created = []

        for data in PROMPT_TEMPLATES:
            obj, was_created = PromptTemplate.objects.get_or_create(
                name=data["name"], defaults={"content_type": data["content_type"], "system_prompt": data["system_prompt"]}
            )
            if was_created:
                created.append(f"PromptTemplate: {obj.name}")

        testimonial, t_created = Asset.objects.get_or_create(
            title=ASSET_TESTIMONIAL["title"],
            defaults={k: v for k, v in ASSET_TESTIMONIAL.items() if k != "title"},
        )
        if t_created:
            created.append(f"Asset: {testimonial.title}")

        writing_sample, w_created = Asset.objects.get_or_create(
            title=ASSET_WRITING_SAMPLE["title"],
            defaults={k: v for k, v in ASSET_WRITING_SAMPLE.items() if k != "title"},
        )
        if w_created:
            created.append(f"Asset: {writing_sample.title}")

        voice, v_created = VoiceProfile.objects.get_or_create(
            name=VOICE_PROFILE["name"],
            defaults={k: v for k, v in VOICE_PROFILE.items() if k != "name"},
        )
        if v_created:
            voice.source_assets.set([testimonial, writing_sample])
            created.append(f"VoiceProfile: {voice.name}")

        blog_template = PromptTemplate.objects.filter(name=f"{PREFIX} Blog post (long-form)").first()

        if not GenerationJob.objects.filter(instructions__startswith=PREFIX).exists():
            page = Page.objects.create(
                title=f"{PREFIX} Why Consistency Beats Frequency",
                content=EXAMPLE_GENERATED_BLOCKS,
            )
            job = GenerationJob.objects.create(
                prompt_template=blog_template,
                voice_profile=voice,
                instructions=f"{PREFIX} Write about why consistency in content matters more than frequency.",
                status="completed",
                result_page=page,
            )
            job.assets.set([testimonial, writing_sample])
            created.append(f"Page + GenerationJob: {page.title}")

        created += self._seed_products()

        if created:
            self.stdout.write(self.style.SUCCESS("Seeded example content:"))
            for line in created:
                self.stdout.write(f"  - {line}")
            self.stdout.write(
                self.style.WARNING(
                    "\nEverything above is prefixed \"[Example]\" and uses fake content. "
                    "Run `python manage.py seed_examples --remove` to delete it all again."
                )
            )
        else:
            self.stdout.write("Example content already exists — nothing to do.")

    def _seed_products(self):
        created = []
        products = []
        for data in PRODUCTS:
            obj, was_created = Product.objects.get_or_create(
                name=data["name"], defaults={k: v for k, v in data.items() if k != "name"}
            )
            products.append(obj)
            if was_created:
                created.append(f"Product: {obj.name}")

        if not FunnelStep.objects.filter(product__in=products, name__startswith=PREFIX).exists():
            FunnelStep.objects.get_or_create(
                product=products[0],
                name=f"{PREFIX} Add the workbook — 40% off",
                defaults={
                    "position": 1,
                    "price_override": "16.00",
                    "is_oto": True,
                    "description": "One-time offer shown right after buying the Content Sprint.",
                },
            )

        if not Sale.objects.filter(notes__startswith=PREFIX).exists():
            today = datetime.date.today()
            for product_index, amount, days_ago in SALES:
                Sale.objects.create(
                    product=products[product_index],
                    amount=amount,
                    date=today - datetime.timedelta(days=days_ago),
                    notes=f"{PREFIX} seeded sale",
                )
            created.append(f"Sales: {len(SALES)} example sale records")

        return created

    def _remove(self):
        counts = {
            "GenerationJob": GenerationJob.objects.filter(instructions__startswith=PREFIX).delete()[0],
            "Page": Page.objects.filter(title__startswith=PREFIX).delete()[0],
            "VoiceProfile": VoiceProfile.objects.filter(name__startswith=PREFIX).delete()[0],
            "Asset": Asset.objects.filter(title__startswith=PREFIX).delete()[0],
            "PromptTemplate": PromptTemplate.objects.filter(name__startswith=PREFIX).delete()[0],
            "Sale": Sale.objects.filter(notes__startswith=PREFIX).delete()[0],
            "FunnelStep": FunnelStep.objects.filter(name__startswith=PREFIX).delete()[0],
            "Product": Product.objects.filter(name__startswith=PREFIX).delete()[0],
        }
        self.stdout.write(self.style.SUCCESS("Removed example content:"))
        for label, count in counts.items():
            self.stdout.write(f"  - {label}: {count}")
