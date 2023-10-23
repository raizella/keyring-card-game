"""
Roadmap:

Functionality Improvements needed:
    (Major) Handling of invalid input
        in my brief testing I have successfully played a game (via cli, prior to switching to api), this can definitely end up in bad states via invalid inputs or inputs at invalid times, i.e. hitting the endpoint in an unintended order will almost certainly cause issues, specifically calling a midgame endpoint before starting game results in attempting to call an attribute of a NoneType, which could be solved by checking if p0 exists and if not redirecting the user to start.
    (Major) Testing
    (Major) Fix issues revealed by tests
    (Major) Security
    (Minor in term of fix time, Major impact) (Bug see detail below) Check win after every attack

Code style / cleanliness Improvements needed: 
    (Major) There's a lot of low hanging fruit for a refactor, I have begun but have barely begun to abstract out duplicate logic
    (Medium) Add more documentation and code comments
        For the sake of time, make mostly # comments for basic readability but would replace with docstrings

    More minor things I wouldn't have done/would fix if not for time constraints:
    Though I initially set out to do so, I partway through abandoned the plan of not hardcoding player vs/ computer diferences

UI improvements needed:
    Instructions (Both write them and provide them to the user (Ideally a separate page linked to from each page, or just as it's own endpoint))

    Note remaining Money after each purchase

    make output html with possible next plays as links

Known remaining bugs: incomplete list (based on my look at the code, many more remain, but alas, timing)
    Computer is incorrectly declared winner if both player and computer die in one round (imo, should be a draw since player went first but would probably run it by product before making that call IRL)

    
Wish list of possible feature improvements:
make a nice web frontend,
keep track of wins between games
add two player mode

If allocated between 2.5 strong python developers (I'm assuming the .5 means that developer spends half their time working on other things), let's call them A,B, and C with C being the .5
Would probably be best to split work up roughly along lines of assigning developer A the API portion (security, not accepting invalid input), B the refactor, C bug fixes, end to end tests, and code review of A and B (plus writing additional test cases if time permits), with each of them being responsible for testing and commenting/documenting their own code.
That will probably end up with the most work on B so A and C can take on a larger part of the testing load if they finish thier parts before B.

All time estimates assume time from task assignment to code is in production, i.e. includes code review, deployment, etc and assume normal operating conditions
My educated guestimate on timing would be that A's work (API, input validation, security) takes about two weeks (varies greatly on whether this is a publically facing endpoint and what's on the other side of it. In lax security scenarios, i.e. if it's a server that just runs a game just for fun and has nothing secret on it and so you're only concerned about valid game states, or it's an internal api, could be a week or less)
B's work will probably also be about two weeks, since most of the code and test writing and correcting burden fall on them, but depends on how thurough they want to be
Ideally C would knock out the bug fixes quickly, if the whatever the other .5 responsibility is permits, otherwise they'll have merge conflict issues with B. If you're optimizing for developer time (see paragraph on tradeoffs below), then ideally C would do bug fixes while B writes tests and neither will step on each other's toes. But in real life, developers whose time is theoretically split 50/50 often find the actual percentage varies is rather different or varies wildly from week to week so I've tried to give C a load was allocated such that they'd also be done in two weeks, but I'm less confident in that.

I've tried to be generous with my estimates here, but to be on the safe side, I think a week of buffer time is good practice and it's always better to be earlier than expected than later than expected, so you should probably estimate that it'll take 3 weeks and actually expect it in about a month.

There's an allocation tradeoff here. On the one hand, bug fixes are highest priority and should be pretty quick, on the other hand, refactoring will probably solve a number of them all on it's own and needs to be done anyway, so if you're optimizing for developer time, and/or product isn't launched yet, you should refactor and test first. However if product is launched and/or you're shooting for an MVP, then you want to prioritize incremental improvements and should do bug fixes first.


P.S. I ran out of time so this was all completed in about 6 hours, so please excuse how hastily hacked together it is.

Notes:

To add: instructions (that print if you press h or something)

Should bought cards appear in hand? - no

Note it when player is attacked

Print available money in buy cards screen

check win after every attack -decided against 

finish refactoring code

add tests

fix issues revealed by tests

verify security of api (make it resilient against invalid input)

make output html with possible next plays as links

command line -> API, replace all input with api input, replace all prints with API outputs

Game plan:
get partially refactored code working as command line game
make it into API

Wish list:
make a nice web frontend,
keep track of wins between games
add two player mode
"""

import itertools, random
from typing import List, Tuple

"""Method that would be removed if code was cleaner but is here for now for the sake of replacing prints quickly"""
def appendWithNewLine(str1, str2) -> str:
    if type(str2) != str:
        str2 = str(str2)
    return str1 + str2 + "<br>"


class Card(object):
    def __init__(self, name, values=(0, 0), cost=1, clan=None):
        self.name = name
        self.cost = cost
        self.values = values
        self.clan = clan

    def __str__(self):
        return "Name %s costing %s with attack %s and money %s" % (
            self.name,
            self.cost,
            self.values[0],
            self.values[1],
        )

    def get_attack(self):
        return self.values[0]

    def get_money(self):
        return self.values[1]


class Player(object):
    def __init__(
        self,
        name: str,
        health: int = 30,
        deck: List[Card] = [],
        hand: List[Card] = [],
        active: List[Card] = [],
        handsize: int = 5,
        discard: List[Card] = [],
        text_name: str = "",
        text_pronoun: str = "",
    ):
        self.name: str = name
        self.health: int = health
        self.deck: List[Card] = deck
        if not self.deck:
            self.deck = self.defaultDeck()
        self.hand: List[Card] = hand
        self.active: List[Card] = active
        self.handsize: int = handsize
        self.discard: List[Card] = discard
        self.money: int = 0
        self.attack: int = 0
        self.text_name: str = text_name
        self.text_pronoun: str = text_pronoun

    # todo verify resulting decks don't have same pointer
    def defaultDeck(self) -> List[Card]:
        deck = [8 * [Card("Serf", (0, 1), 0)], 2 * [Card("Squire", (1, 0), 0)]]
        return list(itertools.chain.from_iterable(deck))

    # Draw player's hand, todo refactor to use deal instead
    def drawHand(self):
        for x in range(0, self.handsize):
            # if deck runs out of cards, replace with shuffled discard pile
            if len(self.deck) == 0:
                random.shuffle(self.discard)
                self.deck = self.discard
                self.discard = []
            card = self.deck.pop()
            self.hand.append(card)

    def discardHand(self):
        self.discard.extend(self.hand)
        self.hand = []


class CardGame(object):
    def __init__(self):
        self.p0: Player = None
        self.pC: Player = None
        self.central = None
        self.aggressive = False

    def start(self, aggressive) -> str:
        text_output = ""
        self.aggressive = aggressive
        self.p0 = Player(name="player one", text_name="Player", text_pronoun="Your")
        self.pC = Player(
            name="player computer", text_name="Computer", text_pronoun="Computer's"
        )
        self.central = {
            "name": "central",
            "active": None,
            "activeSize": 5,
            "supplement": None,
            "deck": None,
        }
        sdc = [
            4 * [Card("Archer", (3, 0), 2)],
            4 * [Card("Baker", (0, 3), 2)],
            3 * [Card("Swordsman", (4, 0), 3)],
            2 * [Card("Knight", (6, 0), 5)],
            3 * [Card("Tailor", (0, 4), 3)],
            3 * [Card("Crossbowman", (4, 0), 3)],
            3 * [Card("Merchant", (0, 5), 4)],
            4 * [Card("Thug", (2, 0), 1)],
            4 * [Card("Thief", (1, 1), 1)],
            2 * [Card("Catapault", (7, 0), 6)],
            2 * [Card("Caravan", (1, 5), 5)],
            2 * [Card("Assassin", (5, 0), 4)],
        ]

        # todo figure out what supplement is
        supplement = 10 * [Card("Levy", (1, 2), 2)]
        deck = list(itertools.chain.from_iterable(sdc))
        random.shuffle(deck)
        self.central["deck"] = deck
        self.central["supplement"] = supplement
        self.central["active"] = []

        max = self.central["activeSize"]
        # todo replace while loop with for loop
        count = 0
        while count < max:
            card = self.central["deck"].pop()
            self.central["active"].append(card)
            count = count + 1

        self.p0.hand = []
        self.pC.hand = []

        self.p0.drawHand()
        self.pC.drawHand()

        text_output += "Available Cards <br>"
        for card in self.central["active"]:
            text_output += card.__str__() + " <br>"

        text_output = appendWithNewLine(text_output, "Supplement")
        if len(self.central["supplement"]) > 0:
            text_output = appendWithNewLine(text_output, self.central["supplement"][0])

        text_output += self.startPlayerOneTurn()
        return text_output

    def startPlayerOneTurn(self) -> str:
        text_output = ""
        self.p0.money = 0
        self.p0.attack = 0
        text_output += self.promptPlayerOneMainTurn()
        return text_output

    # display info and prompt for action
    def promptPlayerOneMainTurn(self) -> str:
        text_output = ""
        text_output = appendWithNewLine(
            text_output, "<br>Player Health %s" % self.p0.health
        )
        text_output = appendWithNewLine(
            text_output, "Computer Health %s" % self.pC.health
        )

        text_output = appendWithNewLine(text_output, "<br>Your Hand")
        for index, card in enumerate(self.p0.hand):
            text_output = appendWithNewLine(text_output, "[%s] %s" % (index, card))
            index = index + 1
        text_output = appendWithNewLine(text_output, "<br>Your Values")
        text_output = appendWithNewLine(
            text_output, "Money %s, Attack %s" % (self.p0.money, self.p0.attack)
        )
        text_output = appendWithNewLine(
            text_output,
            "<br>Choose Action: (P = play all, [0-n] = play that card, B = Buy Card, A = Attack, E = end turn)",
        )
        return text_output

    def playerMoveMainTurn(self, act: str) -> str:
        text_output = ""
        if act == "P":
            if len(self.p0.hand) > 0:
                for x in range(0, len(self.p0.hand)):
                    card = self.p0.hand.pop()
                    self.p0.active.append(card)
                    self.p0.money = self.p0.money + card.get_money()
                    self.p0.attack = self.p0.attack + card.get_attack()

            # todo this does not need to be in this if statement
            text_output = appendWithNewLine(text_output, "<br>Your Hand")
            index = 0
            for card in self.p0.hand:
                text_output = appendWithNewLine(text_output, "[%s] %s" % (index, card))
                index = index + 1

            text_output = appendWithNewLine(text_output, "<br>Your Active Cards")
            for card in self.p0.active:
                text_output = appendWithNewLine(text_output, card)
            text_output = appendWithNewLine(text_output, "<br>Your Values")
            text_output = appendWithNewLine(
                text_output, "Money %s, Attack %s" % (self.p0.money, self.p0.attack)
            )
        if act.isdigit():
            if int(act) < len(self.p0.hand):
                self.p0.active.append(self.p0.hand.pop(int(act)))
                for card in self.p0.active:
                    self.p0.money = self.p0.money + card.get_money()
                    self.p0.attack = self.p0.attack + card.get_attack()
            text_output = appendWithNewLine(text_output, "<br>Your Hand")
            index = 0
            for card in self.p0.hand:
                text_output = appendWithNewLine(text_output, "[%s] %s" % (index, card))
                index = index + 1

            text_output = appendWithNewLine(text_output, "<br>Your Active Cards")
            for card in self.p0.active:
                text_output = appendWithNewLine(text_output, card)
            text_output = appendWithNewLine(text_output, "<br>Your Values")
            text_output = appendWithNewLine(
                text_output, "Money %s, Attack %s" % (self.p0.money, self.p0.attack)
            )
        if act == "B":
            text_output += self.promptPlayerOneBuyScreen()
            return text_output
        if act == "A":
            self.pC.health = self.pC.health - self.p0.attack
            self.p0.attack = 0
        if act == "E":
            if len(self.p0.hand) > 0:
                for x in range(0, len(self.p0.hand)):
                    self.p0.discard.append(self.p0.hand.pop())

            if len(self.p0.active) > 0:
                for x in range(0, len(self.p0.active)):
                    self.p0.discard.append(self.p0.active.pop())
            for x in range(0, self.p0.handsize):
                if len(self.p0.deck) == 0:
                    random.shuffle(self.p0.discard)
                    self.p0.deck = self.p0.discard
                    self.p0.discard = []
                card = self.p0.deck.pop()
                self.p0.hand.append(card)
            # computer turn
            text_output = appendWithNewLine(text_output, self.computerTurn())
            return text_output
        text_output = appendWithNewLine(text_output, "Available Cards")
        for card in self.central["active"]:
            text_output = appendWithNewLine(text_output, card)

        text_output = appendWithNewLine(text_output, "Supplement")
        if len(self.central["supplement"]) > 0:
            text_output = appendWithNewLine(text_output, self.central["supplement"][0])

        text_output = appendWithNewLine(
            text_output, "<br>Player Health %s" % self.p0.health
        )
        text_output = appendWithNewLine(
            text_output, "Computer Health %s" % self.pC.health
        )
        text_output += self.promptPlayerOneMainTurn()
        return text_output

    def promptPlayerOneBuyScreen(self) -> str:
        text_output = ""
        text_output = appendWithNewLine(text_output, "Available Cards")
        ind = 0
        for card in self.central["active"]:
            text_output = appendWithNewLine(text_output, "[%s] %s" % (ind, card))
            ind = ind + 1
        text_output = appendWithNewLine(
            text_output,
            "Choose a card to buy [0-n], S for supplement, E to end buying",
        )
        text_output += "Choose option: "
        # todo add links
        return text_output

    def playerOneMoveBuyScreen(self, bv) -> str:
        text_output = ""
        if bv == "S":
            if len(self.central["supplement"]) > 0:
                if self.p0.money >= self.central["supplement"][0].cost:
                    self.p0.money = self.p0.money - self.central["supplement"][0].cost
                    self.p0.discard.append(self.central["supplement"].pop())
                    text_output = appendWithNewLine(text_output, "Supplement Bought")
                else:
                    text_output = appendWithNewLine(
                        text_output, "insufficient money to buy"
                    )
            else:
                text_output = appendWithNewLine(text_output, "no supplements left")
        elif bv == "E":
            # this variable was never used so I'm commenting it out but todo check if this was important
            # notending = False
            return self.promptPlayerOneMainTurn()
        elif bv.isdigit():
            if int(bv) < len(self.central["active"]):
                if self.p0.money >= self.central["active"][int(bv)].cost:
                    self.p0.money = self.p0.money - self.central["active"][int(bv)].cost
                    self.p0.discard.append(self.central["active"].pop(int(bv)))
                    if len(self.central["deck"]) > 0:
                        card = self.central["deck"].pop()
                        self.central["active"].append(card)
                    else:
                        self.central["activeSize"] = self.central["activeSize"] - 1
                    text_output = appendWithNewLine(text_output, "Card bought")
                else:
                    text_output = appendWithNewLine(
                        text_output, "insufficient money to buy"
                    )
            else:
                text_output = appendWithNewLine(
                    text_output, "enter a valid index number"
                )
        else:
            text_output = appendWithNewLine(text_output, "Enter a valid option")
        if self.p0.money > 0:
            text_output += self.promptPlayerOneBuyScreen()
            return text_output
        else:
            text_output += self.promptPlayerOneMainTurn()
            return text_output

    # plays computers moves then checks if game over, if so, back to home, else, promptMainTurn
    def computerTurn(self) -> str:
        text_output = ""
        money = 0
        attack = 0
        for x in range(0, len(self.pC.hand)):
            card = self.pC.hand.pop()
            self.pC.active.append(card)
            money = money + card.get_money()
            attack = attack + card.get_attack()

        text_output = appendWithNewLine(
            text_output, " Computer player values attack %s, money %s" % (attack, money)
        )
        text_output = appendWithNewLine(
            text_output, " Computer attacking with strength %s" % attack
        )
        self.p0.health = self.p0.health - attack
        attack = 0
        text_output = appendWithNewLine(
            text_output, "<br>Player Health %s" % self.p0.health
        )
        text_output = appendWithNewLine(
            text_output, "Computer Health %s" % self.pC.health
        )
        text_output = appendWithNewLine(
            text_output, " Computer player values attack %s, money %s" % (attack, money)
        )
        text_output = appendWithNewLine(text_output, "Computer buying")
        if money > 0:
            cb = True
            templist = []
            text_output = appendWithNewLine(
                text_output, "Starting Money %s and cb %s " % (money, cb)
            )
            #todo get rid of need for this
            central = self.central
            while cb:
                templist = []
                if len(central["supplement"]) > 0:
                    if central["supplement"][0].cost <= money:
                        templist.append(("S", central["supplement"][0]))
                for intindex in range(0, central["activeSize"]):
                    if central["active"][intindex].cost <= money:
                        templist.append((intindex, central["active"][intindex]))
                if len(templist) > 0:
                    highestIndex = 0
                    for intindex in range(0, len(templist)):
                        if templist[intindex][1].cost > templist[highestIndex][1].cost:
                            highestIndex = intindex
                        if templist[intindex][1].cost == templist[highestIndex][1].cost:
                            if self.aggressive:
                                if (
                                    templist[intindex][1].get_attack()
                                    > templist[highestIndex][1].get_attack()
                                ):
                                    highestIndex = intindex
                            else:
                                if (
                                    templist[intindex][1].get_attack()
                                    > templist[highestIndex][1].get_money()
                                ):
                                    highestIndex = intindex
                    source = templist[highestIndex][0]
                    if source in range(0, 5):
                        if money >= central["active"][int(source)].cost:
                            money = money - central["active"][int(source)].cost
                            card = central["active"].pop(int(source))
                            text_output = appendWithNewLine(
                                text_output, "Card bought %s" % card
                            )
                            self.pC.discard.append(card)
                            if len(central["deck"]) > 0:
                                card = central["deck"].pop()
                                central["active"].append(card)
                            else:
                                central["activeSize"] = central["activeSize"] - 1
                        else:
                            text_output = appendWithNewLine(
                                text_output, "Error Occurred"
                            )
                    else:
                        if money >= central["supplement"][0].cost:
                            money = money - central["supplement"][0].cost
                            card = central["supplement"].pop()
                            self.pC.discard.append(card)
                            text_output = appendWithNewLine(
                                text_output, "Supplement Bought %s" % card
                            )
                        else:
                            text_output = appendWithNewLine(
                                text_output, "Error Occurred"
                            )
                else:
                    cb = False
                if money == 0:
                    cb = False
        else:
            text_output = appendWithNewLine(text_output, "No Money to buy anything")

        if len(self.pC.hand) > 0:
            for x in range(0, len(self.pC.hand)):
                self.pC.discard.append(self.pC.hand.pop())
        if len(self.pC.active) > 0:
            for x in range(0, len(self.pC.active)):
                self.pC.discard.append(self.pC.active.pop())
        for x in range(0, self.pC.handsize):
            if len(self.pC.deck) == 0:
                random.shuffle(self.pC.discard)
                self.pC.deck = self.pC.discard
                self.pC.discard = []
            card = self.pC.deck.pop()
            self.pC.hand.append(card)
        text_output = appendWithNewLine(text_output, "Computer turn ending")

        text_output = appendWithNewLine(text_output, "Available Cards")
        for card in central["active"]:
            text_output = appendWithNewLine(text_output, card)

        text_output = appendWithNewLine(text_output, "Supplement")
        if len(central["supplement"]) > 0:
            text_output = appendWithNewLine(text_output, central["supplement"][0])

        text_output = appendWithNewLine(
            text_output, "<br>Player Health %s" % self.p0.health
        )
        text_output = appendWithNewLine(
            text_output, "Computer Health %s" % self.pC.health
        )
        game_over, game_result = self.checkWin()
        if game_over:
            text_output = appendWithNewLine(text_output, game_result)
            text_output += 'Do you want to play again?<br> <a href="/opponentSelection"> Yes </a>'
            return text_output
        else:
            text_output += self.startPlayerOneTurn()
            return text_output

    def checkWin(self) -> Tuple[bool, str]:
        text_output = ""
        if self.p0.health <= 0 and self.pC.health > 0:
            text_output = appendWithNewLine(text_output, "Computer wins")
            return True, text_output
        elif self.pC.health <= 0 and self.p0.health > 0:
            text_output = appendWithNewLine(text_output, "Player One Wins")
            return True, text_output
        elif self.central["activeSize"] == 0 or (
            self.pC.health <= 0 and self.p0.health <= 0
        ):
            if self.central["activeSize"] == 0:
                text_output = appendWithNewLine(text_output, "No more cards available")
            # tie breaker
            if self.p0.health > self.pC.health:
                text_output = appendWithNewLine(
                    text_output, "Player One Wins on Health"
                )
            elif self.pC.health > self.p0.health:
                text_output = appendWithNewLine(text_output, "Computer Wins")
            else:
                pHT = 0
                pCT = 0
                if pHT > pCT:
                    text_output = appendWithNewLine(
                        text_output, "Player One Wins on Card Strength"
                    )
                elif pCT > pHT:
                    text_output = appendWithNewLine(
                        text_output, "Computer Wins on Card Strength"
                    )
                else:
                    text_output = appendWithNewLine(text_output, "Draw")
            return True, text_output
        else:
            return False, ""

    """ Deals numCards cards from fromDeck to toDeck, if fromDeck runs out, shuffle backupDeck and replace fromDeck with backupDeck (emptying backupDeck)"""

    def deal(fromDeck: List[Card], toDeck: List[Card], numCards: int, backupDeck=None):
        for x in range(0, numCards):
            # if deck runs out of cards, replace with shuffled discard pile
            if len(fromDeck) == 0:
                random.shuffle(backupDeck)
                fromDeck = backupDeck
                backupDeck = []
            card = fromDeck.pop()
            toDeck.append(card)

if __name__ == "__main__":
    print("Command line interface no longer supported, use api instead")
    exit()
