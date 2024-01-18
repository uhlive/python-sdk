import asyncio
import os

from async_bot_lib import Bot

from uhlive.stream.recognition import CompletionCause as CC
from uhlive.stream.recognition import RecognitionComplete, StartOfInput


class DemoBot(Bot):
    async def set_defaults(self):
        await self.set_params(
            speech_language="fr",
            no_input_timeout=5000,
            recognition_timeout=20000,
            speech_complete_timeout=1200,
            speech_incomplete_timeout=2000,
            speech_nomatch_timeout=3000,
        )

        # Define grammars up front
        await self.define_grammar(
            "speech/keywords?alternatives=allo\\-media", "activation"
        )
        await self.define_grammar(
            "speech/keywords?alternatives=adresse|multi|arrêt", "menu"
        )
        await self.define_grammar(
            "speech/spelling/mixed?regex=[a-z][0-9]{3}[a-z]", "subs_num"
        )

    async def wait_activation(self):
        # Wait for Activation
        print('Say "allo-media" to start.')
        while True:
            await self.recognize(
                "session:activation",
                hotword_max_duration=10000,
                no_input_timeout=50000,
                recognition_mode="hotword",
            )
            resp = await self.expect(RecognitionComplete)
            if resp.completion_cause == CC.Success:
                break
            print(".")

        await self.say("Lancement de la démonstration")

    async def demo_address(self):
        say = self.say
        await say("Donnez moi une adresse")
        await self.recognize("builtin:speech/postal_address")
        resp = await self.expect(RecognitionComplete, ignore=(StartOfInput,))
        print(resp.completion_cause)
        result = resp.body
        if result.asr is None:
            await say("Je n'ai rien entendu. Laissez tomber.")
        elif result.nlu is None:
            await say("je n'ai pas compris. Tant pis!")
            print("user said", result.asr.transcript)
        else:
            addr = result.nlu.value
            if not addr["zipcode"]:
                nlu = await self.ask_until_success(
                    "Quel est le code postal ?",
                    "builtin:speech/zipcode",
                    recognition_mode="hotword",
                )
                addr["zipcode"] = nlu.value
            formatted = f"j'ai compris {addr['number'] or ''} {addr['street'] or ''} {addr['zipcode'] or ''} {addr['city'] or ''}"
            await say(formatted)
            confirm = await self.confirm(
                "Est-ce correct?",
            )
            if confirm:
                await say("J'envoie dans le CRM")
                print("CRM>", addr)
            else:
                await say("tu prononces tellement mal!")
                print(result.asr.transcript)

    async def demo_multi(self):
        say = self.say
        while True:
            await say(
                "Donnez moi votre numéro d'abonné : une lettre, trois chiffres une lettre, si vous en avez un"
            )
            await self.recognize("session:subs_num", "builtin:speech/boolean")
            resp = await self.expect(RecognitionComplete, ignore=(StartOfInput,))
            print(resp.completion_cause)
            result = resp.body
            if result.asr is None:
                await say("Je n'ai rien entendu.")
                continue
            elif result.nlu is None:
                await say("je n'ai pas compris.")
                print("user said", result.asr.transcript)
                continue
            if "boolean" in result.nlu.type and result.nlu.value:
                await say("Vous êtes abonné, vous avez donc un numéro d'abonné.")
                continue
            if "spelling" in result.nlu.type:
                verif = " ".join(result.nlu.value)
                await say(f"J'ai compris {verif}")
                confirm = await self.confirm("Est-ce correct ?")
                if confirm:
                    break
                else:
                    continue

            break
        nlu = result.nlu
        if "boolean" in nlu.type:
            await say("Je vous passe le service commercial")
        else:
            await say("je vous passe le services des abonnés")

    async def scenario(self):
        # Shortcuts
        say = self.say

        # Scenario
        await self.set_defaults()
        await self.wait_activation()

        # dialogue
        while True:
            nlu = await self.ask_until_success(
                "Que voulez vous tester ? Adresse ou multi grammaire ?",
                "session:menu",
                hotword_max_duration=10000,
                no_input_timeout=5000,
                recognition_mode="hotword",
            )

            keyword = nlu.value
            if keyword == "adresse":
                await self.demo_address()
            elif keyword == "multi":
                await self.demo_multi()
            elif keyword == "arrêt":
                break

        await say("Salut ! à la prochaine !")


if __name__ == "__main__":
    uhlive_client = os.environ["UHLIVE_API_CLIENT"]
    uhlive_secret = os.environ["UHLIVE_API_SECRET"]
    bot = DemoBot(os.environ["GOOGLE_TTF_KEY"])
    asyncio.run(bot.run(uhlive_client, uhlive_secret))
