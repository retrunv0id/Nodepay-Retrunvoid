# NodePlay - VPS

to run the code, you need to install the following packages:

```bash
git clone https://github.com/retrunv0id/Nodepay-Retrunvoid
cd Nodepay-Retrunvoid
pip install -r requirements.txt
```
## Configuration
#Get NP_TOKEN
1. Go to [NodePlay](https://app.nodepay.ai/register?ref=yyk8pF3JHwKj6Rl)
2. Sign in with your account
3.Inspect Element and go to the Console tab
4. Type `localStorage.getItem('np_token');` and press Enter

#Add NP_TOKEN to the code
1. Open `main.py` in a text editor
2. Replace token_info = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNjEwMjIwNzY' with your NP_TOKEN

## Usage
```bash
python3 main.py
```
