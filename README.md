# Ball IQ
## 1. Project Overview

- **Company Name**: Ball IQ
- **Group X**: João Ferreira, Miguel Mendes, Rodrigo Maia, Artem Khomytskyi, Tymofii Kuzmenko
- **Description**:  
Our company is a EPL fantasy football related one, therefore our chatbot's main objective is to address some user queries, it will give informative responses to questions, like recommending players to buy, optimizing the user's lineup, knowing some player's stats for this season, knowing the next matches for players, explaining what some stats are and how they affect players' fantasy points, knowing some information about our company Ball IQ and allowing user's to update or view their  teams fantasy points. It will also allow user's to make changes to their team either by transferring players in and out or by benching and bringing players in from their bench. This changes will only be available in our database and not on the EPL fantasy football website. 
---

## 2. How to Test the Chatbot

### 2.1 Prerequisites

- **Python Version**: 3.12.7 
- **Dependencies**:  
  All in the requirements.txt file.
  
- **Environment Setup**:  
  Install the libraries in the requirements.txt file and their specific versions. Then open the project folder on visual studio, and if you are having trouble with imports from .py files in other directories use the terminal to run the following code: **pip install -e .**, make sure you are in the same directory as the setup.py file when you run this. After that there should be no more problem with imports of files from other directories.

- **Link for chatbot app**:
  Instead of creating an environment and running everything in code you can just go to balliq.streamlit.app and test our chatbot in the oficial streamlit created app.


### 2.2 How to Run the Chatbot

When testing the chatbot if everything is done well in the setup phase, you can just run the chat_bot_tester.py file as it is already running, if you decide to use any other user that is not user 11, only users 1 to 10 are also available the other two variables fell free to change as long as they keep their string format. Although user 11 is the recommended one as is the one with the most data.

You can also test in main_app.py or in the website, where you will need to first register and then log in with your new account to use the chatbot functionalities.

## 3. Database Schema

### 3.1 Database Overview and Schema Diagram

![image](https://github.com/user-attachments/assets/a73d32ca-591d-42d3-be85-6b0f4d98ab3e)

In the fixtures table there is no match_id variable as we decided to make a primary key composed of week, home_team and away_team to assure that there would be no duplicates.

### 3.2 Table Descriptions

Table 1 - user_team:
- user_id: ID of the user, unique for each user
- player_id: ID of the player, unique for each player
- starting_eleven: Boolean (0 or 1) where 0 represents that the player is not in the starting eleven and 1 represents that the player is in the starting eleven
- on_team: Boolean (0 or 1) where 0 represents that the player is not in the user's team and 1 represents that the player is on the user's team

Table 2 - users:
- user_id: ID of the user, unique for each user
- username: Name which the user wants be be called
- email: User's email
- password: User's password
- team_name: Name of the user's team
- budget: Budget of their team, money available to buy players
- points: Fantasy points of their team, defined to be the same as the ones on EPL fantasy football website by allowing the user to update them

Table 3 - player_stats:
- player_id: ID of the player, unique for each player
- goals: Number of goals scored by the player this season
- assists: Number of assists provided by the player this season
- yellow_cards: Number of yellow cards gotten by the player this season
- red_cards: Number of red cards gotten by the player this season
- penalties_defended: Number of penalties defended by the player, most common on goalkeepers
- own_goals: Number of own goals scored by the plater this season
- clean_sheets: Number of games where the team the player plays for did not concede a goal
- saves: Number of shots defended by the player, most common on goalkeepers
- starts: Number of games where the player was on the starting 11
- penalties_missed: Number of penalties a player failed to score

Table 4 - players_fantasy:
- player_id: ID of the player, unique for each player
- name: Player's name
- team: Player's team, real life team like Manchester United, Chelsea, ...
- position: Player's position either goalkeeper, defender, midfielder or forward
- price: Player's price on fantasy football
- price_evolution: Change in price from the start of the season
- points_per_game: Average fantasy points the player has per game
- form_rank: Rank based on the current form of the players, the lower the better
- total_fantasy_points: Total fantasy points the player has this season so far
- next_week: Football week number of the next matches
- expected_points_next_game: Number of points the player is expected to do in his next match

Table 5 - fixtures:
- week: Week number of the matches
- date: Date when the match occurs
- home_team: Team that plays in their stadium, with home advantage
- away_team: The team on the road, without home advantage
---

## 4. User Intentions

### 4.1 Implemented Intentions

List and briefly describe the user intentions that the chatbot is designed to handle. For example:

- **Check Upcoming Fixtures**: User requests details about the next matches of a player or the matches to be played in some week.
- **Optimize Lineup**: User requests optimization of his lineup, suggestions on what are the best players on their team for him to put in his starting 11.
- **Putting Player in starting 11**: User intends to make a change on his starting 11 either by benching a player of bringing in a new one.
- **Know Information about a Stat**: User requests information about a stat itself (example: "What is a goal?") or also asks how a certain stat affect player points (example: "How many points a midfielder gets for scoring a goal?").
- **Know Information abou Ball IQ (our company)**: User requests information about Ball IQ (example: "What sets Ball IQ apart from other companies?").
- **Recommend Players**: User requests recommendations about players he should buy for his team, players that aren't already in his team but that he can get to improve it.
- **Transfer Player**: User intends to make a change on his squad either by adding a new player to his team (especially useful when he is creating his team as it allows to add one by one until he has the limit of 15 players) or by removing a player from his team and replace him with another one.
- **View or Actualize Team Points**: User requests to see how many fantasy points his team has or intends to actualize them by providing the new amout of points he has in order for the points to be up to date with his fantasy.
- **View Player Stats and Price Evolution**: User requests to get the stats of a certain player this season as well as seeing the price evolution and the form rank (the user can choose which stats to see or just see them all for the player chosen).
- **Chitchat**: Not really an user intention but the chatbot is able to handle chitchat from the user and try to redirect them into asking something else where the chatbot can be useful.

### 4.2 How to Test Each Intention

For each intention, provide 3 examples of test messages that users can use to verify the chatbot's functionality. Include both typical and edge-case inputs to ensure the chatbot handles various scenarios.

#### Check Upcoming Fixtures

**Test Messages:**

1. "What are the games Bruno Fernandes will play after week 23?"
2. "What are the next games for Dalot?"
3. "Who will Cole Palmer face next week?"

**Expected Behavior:**  
The chatbot should retrieve and present information about the matches asked for a specific player, like the teams playing and the date, the default is showing only the next 2 games.

#### Optimize Lineup

**Test Messages:**

1. "Make me the best team possible to play in 343, do not include Saka."
2. "What players should I choose for a 4-3-3?"
3. "I want to get the best lineup for my players, 2 midfielders, 3 forwards, 5 defenders."

**Expected Behavior:**  
The chatbot should check if there is a specific tactic he needs to follow. If there is, he should follow that, if not it should provide the best players for a 433 tactic.

#### Putting Players in Starting 11

**Test Messages:**

1. "Take Bruno Fernandes out of my starting 11"
2. "Put Cole Palmer in my lineup"
3. "Remove Cole Palmer from my starters"

**Expected Behavior:**  
The chatbot allows the user to make changes in their starters, adding the player after checking he is on the user's team and not already in the starting 11 or benching the player after checking he is in the user's team and in the starting 11.

#### Know Information about Stats

**Test Messages:**

1. "What is a goal?"
2. "How does an assist affect my fantasy player's points, how many points do they get"
3. "How many fantasy points does a goal value?"

**Expected Behavior:**  
The chatbot allows the user to get information about stats and fantasy points related questions, by leveraging RAG to get the information from pdfs available to the chatbot.

#### Know Information about Ball IQ (our company)

**Test Messages:**

1. "What sets Ball IQ apart from their competitors?"
2. "What are the main goals of Ball IQ?"
3. "What is Ball IQ mission statement?"

**Expected Behavior:**  
The chatbot allows the user to get information about the Ball IQ company, by leveraging RAG to get the information from pdfs available to the chatbot.

#### Recommend Players

**Test Messages:**

1. "I want the top 1 best goalkeeper to buy"
2. "Give me the best forward I can buy for my team for under 10$"
3. "Recommend me the best players to buy for my team"

**Expected Behavior:**  
The chatbot should check what players are already on the user's team and recommend the best ones out of the ones that are not there. Giving valuable suggestions to the user under budget or position constraints.

#### Transfer Player

**Test Messages:**

1. "I want to take MAteta out of my team and bring in Halland" 
2. "Sell Porro and buy Luiz Dias"
3. "Sign Saka to the squad"

**Expected Behavior:**  
The chatbot should check whether the user wants to just bring in one player, or to bring in one player while dropping another one. Regarding the incoming player, the chatbot should check if he is not already in the team, regarding the outgoing it should check if he is in the team. In both cases whether is just buying a player or swapping the chatbot should check if the user has enough budget for that

#### View or Actualize Team Points

**Test Messages:**

1. "What are my current points?"
2. "Change my points to 100"
3. "How many points does my team have so far?"

**Expected Behavior:**  
The chatbot should check what action the user wants to perform, whether is just viewing or updating and act accordingly. If it is view it should provide the user with a message where their points are presented, if it is update it should do the update to the number of points provided by the user and reply with a message telling them it was a successful update and how many points they have

#### View Player Stats and Price Change

**Test Messages:**

1. "I want to get the stats about Diaz"
2. "How many goals did Saka scored?"
3. "Tell me the number of goals and assists Mateta has this season"

**Expected Behavior:**  
The chatbot should check if the player provided exists indeed and the give the users the information the asked for. The chatbot will also give the user information about how is the player the asked about doing compared to the average player in a similar position

#### Chitchat

**Test Messages:**

1. "Did you see the Lakers game yesterday? Crazy clutch block by the Goat."
2. "Is it going to be sunny tomorrow or will it be raining?"
3. "Today I'm felling excited, what about you?"

**Expected Behavior:**  
The chatbot should answer to the user in a way that will try to redirect them to ask questions about EPL fantasy football.

---

## 5. Intention Router

### 5.1 Intention Router Implementation

- **Message Generation**:  
  The training messages were generated synthetically using OpenAI, there are at least 50 for each intention, 25 for messages about the company and 25 chitchat messages labeled as none. The test messages were generated manually and there are 3 for each intention, including about the company and chitchat labeled as none, which corresponds to a split of almost 90/10, it would be something around 91/9. 
  All messages, both manually and synthetically generated, are stored in json files under the names of synthetic_intentions and new_intentions.

### 5.2 Semantic Router Training

- **Hyperparameters**:  
  We tried using the HuggingFaceEncoder and the OpenAIEncoder and both performed very similarly. However, we ended up choosing the HuggingFaceEncoder.  
  The aggregation method used was "max" and the top k was the default.

### 5.3 Post-Processing for Accuracy Improvement

- **Post-Processing Techniques**:  
  To get better results we decided to use an LLM, implemented in bot.py that was able to identify to which intention a message is related to when the Route outputs None, we also implemented a constraint in which if the Router is in doubt about 2 intentions or more and the difference between them is less than 0.2, then the LLM will analyze and decide to which route does the message belong to.

---

## 6. Intention Router Accuracy Testing Results

### Methodology

1. **Message Creation**:

   - Generated at least 50 messages per intention, totaling more than 400 messages. These were synthetically generated.
   - Additionally, there were generate at least 25 small-talk messages related to our company and 25 off-topic messages unrelated to the company, labeled as "None."

2. **Data Splitting**:

   - The data was split between data generated synthetically and manually to try and test the data in more human-like messages, the split was very close to a 90/10, ensuring a balanced distribution of each intention.

3. **Training the Semantic Router**:

   - After training the router on the messages generated synthetically we got an accuracy of 100% in the training and of 80% in the test messages.

4. **Post-Processing with LLM**:

   - The preprocessing we have done was just done already in the bot.py file, by using a LLM to help the router decide when the difference between 2 intentions was less than 0.2. Despite the fact that this wasn't trained and tested like we did on the previous step, the results we have seen by trying to use different messages in our bot were of an accuracy that if it wasn't 100% it was very close.

5. **Reporting Results**:
   - These are the results from the router without any help from the LLM

### Results

Present the accuracy results in a table format:

| Intention                            | Test Inputs | Correct | Incorrect | Accuracy (%) |
| ------------------------------------ | ----------- | ------- | --------- | ------------ |
| Check Upcoming Fixtures              | 3           | 2       | 1         | 67%          |
| Optimize Lineup                      | 3           | 3       | 0         | 100%         |
| Putting Players in Starting 11       | 3           | 3       | 0         | 100%         |
| Know Information about Ball IQ       | 3           | 1       | 2         | 33%          |
| Know Information about stats         | 3           | 3       | 0         | 100%         |
| Recommend Players                    | 3           | 3       | 0         | 100%         |
| Transfer Players                     | 3           | 2       | 1         | 67%          |
| View or Update Team Points           | 3           | 3       | 0         | 100%         |
| View Player Stats and Price Change   | 3           | 1       | 2         | 33%          |
| None                                 | 3           | 3       | 0         | 100%         |
| **Average Accuracy**                 | 30          | 24      | 6         | 80%          |

Notes: The failure to predict sometimes Transfer Players, Check Upcoming Fixtures and View Player Stats and Price Change were due to confusion between 2 or more intentions that had a very similar score, it is where our thought for the need of an LLM to help with such cases came from and we saw a very significant improvement after the implementation of the LLM to help the router
The failure to predict Know Information about Ball IQ comes from the fact that the messages generated almost all included "Ball IQ" and when tested we used words like "your company", so the router couldn't really understand they were referring to the same thing. We tried to solve this by asking OpenAI to generate the messages using Ball IQ's name as well as simply "your company", however it would never comply and would use only one of the two for all messages. Therefore we decided to go with messages with Ball IQ in their name as we thought it would be more common when users are referring to our company, which is also solved by the LLM.
The only problem that remains even with the LLM is that some times queries like "I want to sell Salah and buy Bruno Fernandes" are wrongly classified as recommend players instead of transfer players. The model has a hard time getting the intention Transfer Players needing almost always help from the LLM to understand it. Although we have the problem mentioned above, it is only in a limited number of sentences that can be rephrased to get what we want, as the LLM greatly increases the model's accuracy.
```

```
6. **Memory**:

We created this section to explain some memory related questions.

- We implemented a way to store the sessions in a txt file in the directory `chat_history` however this won't be recovered each time a user uses our chatbot as it can easily make `chat_history` too big for the gpt-4o-mini to handle. Giving error codes like: `Error code: 429 - {'error': {'message': 'Request too large for gpt-4o-mini in organization org-yppiHngQem4nJsWAapRvoDRV on tokens per min (TPM): Limit 200000, Requested 274327. The input or output tokens must be reduced in order to run successfully. Visit https://platform.openai.com/account/rate-limits to learn more.', 'type': 'tokens', 'param': None, 'code': 'rate_limit_exceeded'}}`

- To get the chat history from the txt file we used this code (deleted from there as it would lead to problems when chat history becomes too big):
  file_path = f"Ball_IQ/BallIQ/chat_history/{user_id}_{conversation_id}_history.txt" 
              if os.path.exists(file_path): 
                  with open(file_path, "r") as file: 
                      for line in file: 
                          if line.startswith("User: "): 
                              content = line[len("User: "):].strip() 
                              self.store[(user_id, conversation_id)].messages.append(HumanMessage(content)) 
                          elif line.startswith("Bot: "): 
                              content = line[len("Bot: "):].strip() 
                              self.store[(user_id, conversation_id)].messages.append(AIMessage(content))

- The chat_histories that come from the streamlit app won't be stored as txt files as it uses the files from the github repository so it can't add new files to store chat history from users.
