import os

from sync_bot_lib import Bot

from uhlive.stream.recognition import CompletionCause as CC
from uhlive.stream.recognition import RecognitionComplete, StartOfInput
from uhlive.stream.recognition.events import CompletionCause


class DemoBot(Bot):
    def set_defaults(self):
        self.set_params(
            speech_language="fr",
            no_input_timeout=5000,
            recognition_timeout=20000,
            speech_complete_timeout=1000,
            speech_incomplete_timeout=2000,
            speech_nomatch_timeout=4000,
        )

        # Define grammars up front
        self.define_grammar("speech/keywords?alternatives=allo\\-media", "activation")
        self.define_grammar(
            "speech/keywords?alternatives=adresse|multi|arrêt|date", "menu"
        )
        self.define_grammar(
            "speech/spelling/mixed?regex=[a-z][0-9]{3}[a-z]", "subs_num"
        )

    def wait_activation(self):
        # Wait for Activation
        print('Say "allo-media" to start.')
        self.say("En écoute")
        while True:
            self.recognize(
                "session:activation",
                hotword_max_duration=10000,
                no_input_timeout=50000,
                recognition_mode="hotword",
            )
            resp = self.expect(RecognitionComplete)
            if resp.completion_cause == CC.Success:
                break
            print(".")

        self.say("Lancement de la démonstration")

    def demo_address(self):
        say = self.say
        say("Donnez moi une adresse")
        self.recognize("builtin:speech/postal_address")
        resp = self.expect(RecognitionComplete, ignore=(StartOfInput,))
        print(resp.completion_cause)
        result = resp.body
        if result.asr is None:
            say("Je n'ai rien entendu. Laissez tomber.")
        elif result.nlu is None:
            say("je n'ai pas compris. Tant pis!")
            print("user said", result.asr.transcript)
        else:
            addr = result.nlu.value
            if not addr["zipcode"]:
                nlu = self.ask_until_success(
                    "Quel est le code postal ?",
                    "builtin:speech/zipcode",
                    recognition_mode="hotword",
                )
                addr["zipcode"] = nlu.value
            say("J'ai compris")
            if addr['number']:
                say(f"numéro : {addr['number']}")
            if addr['street']:
                say(f"voie : {addr['street']}")
            if addr['zipcode']:
                say(f"code postal : {addr['zipcode']}")
            if addr['city']:
                say(f"ville : {addr['city']}")
            if addr['complement']:
                say(f"complément d'adresse : {addr['complement']}")
            confirm = self.confirm(
                "Est-ce correct?",
            )
            if confirm:
                say("J'envoie dans le CRM")
                print("CRM>", addr)
            else:
                say("tu prononces tellement mal!")
                print(result.asr.transcript)

    def demo_multi(self):
        say = self.say
        while True:
            say(
                "Donnez moi votre numéro d'abonné : une lettre, trois chiffres une lettre, si vous en avez un"
            )
            self.recognize("session:subs_num", "builtin:speech/boolean")
            resp = self.expect(RecognitionComplete, ignore=(StartOfInput,))
            print(resp.completion_cause)
            result = resp.body
            if result.asr is None:
                say("Je n'ai rien entendu.")
                continue
            elif result.nlu is None:
                say("je n'ai pas compris.")
                print("user said", result.asr.transcript)
                continue
            if "boolean" in result.nlu.type and result.nlu.value:
                say("Vous êtes abonné, vous avez donc un numéro d'abonné.")
                continue
            if "spelling" in result.nlu.type:
                verif = " ".join(result.nlu.value)
                say(f"J'ai compris {verif}")
                confirm = self.confirm("Est-ce correct ?")
                if confirm:
                    break
                else:
                    continue

            break
        nlu = result.nlu
        if "boolean" in nlu.type:
            say("Dans ce cas, je vous passe le service commercial")
        else:
            say("je vous passe le services des abonnés")

    def demo_date(self):
        say = self.say
        loop = True
        months = "toto janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split()
        questions = [
            "donnez moi une date",
            "quelle date ?",
            "quel jour ?",
            "à quel moment?",
            "choisissez une date",
            "dites une date",
            "proposez une date",
            "encore une autre",
        ]
        i = 0
        while loop:
            say(questions[i])
            i = (i + 1) % len(questions)
            self.recognize("builtin:speech/date", "builtin:speech/boolean")
            resp = self.expect(RecognitionComplete, ignore=(StartOfInput,))
            result = resp.body
            if result.asr is None:
                say("Je n'ai rien entendu.")
                continue
            elif result.nlu is None:
                say("je n'ai pas compris.")
                print("got", result.asr.transcript, resp)
                continue
            if "boolean" in result.nlu.type and not result.nlu.value:
                break
            if "date" in result.nlu.type:
                date = result.nlu.value
                if date["valid"]:
                    if resp.completion_cause != CompletionCause.Success:
                        say("Date partielle")
                    verif = (
                        f"{date['day'] or ''} {months[date['month']]} {date['year']}"
                    )
                    print(
                        f"Record in CRM: {date['year']}-{date['month']}-{date['day']}"
                    )
                    say(f"J'ai compris {verif}")
                else:
                    say("J'ai compris, mais ce n'est pas une date valide")

    def scenario(self):

        # Scenario
        self.set_defaults()
        self.wait_activation()

        # dialogue
        while True:
            nlu = self.ask_until_success(
                "Que voulez vous tester ? Adresse, date ou multi grammaire ?",
                "session:menu",
                hotword_max_duration=10000,
                no_input_timeout=5000,
                recognition_mode="hotword",
            )

            keyword = nlu.value
            if keyword == "adresse":
                self.demo_address()
            elif keyword == "multi":
                self.demo_multi()
            elif keyword == "date":
                self.demo_date()
            elif keyword == "arrêt":
                break

        self.say("Salut ! à la prochaine !")


if __name__ == "__main__":
    uhlive_client = os.environ["UHLIVE_API_CLIENT"]
    uhlive_secret = os.environ["UHLIVE_API_SECRET"]
    bot = DemoBot(os.environ["GOOGLE_TTF_KEY"])
    bot.run(uhlive_client, uhlive_secret)
