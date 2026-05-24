import os
import time
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

# --- ⚙️ 画面の設定（Config） ---
st.set_page_config(
    page_title="レキーシ先生の歴史クイズ",
    page_icon="🌸",
    layout="centered"
)

st.title("🌸 レキーシ先生の歴史クイズ")
st.caption("レキーシ先生と一緒に、楽しく歴史の重要項目を勉強しよう！")
st.write("---")

# 🔑 Geminiクライアントの準備
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 最強のモデルリスト（草木さん特製バージョンまよ！）
models_to_try = [
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-flash-latest",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite-preview"
]

# 🏫 歴史先生のシステムプロンプト設定
history_config = types.GenerateContentConfig(
    system_instruction="""あなたは子供たちに歴史を教えるのが最高に上手なベテラン先生（レキーシ先生）です。
    日本の歴史の重要項目（色々な年号や出来事、人物）から、ランダムに1問ずつ4択クイズを出題してください。
    
    【ルール】
    1. 一番最初に歴史の面白い話をひとつ入れてください。1回のお返事につき、必ず「1問だけ」出題してください。
     問題は、最初の面白い話に関わるものにしてください。
    　
    2. お返事の最後には、必ず以下の形式でプレイヤーが選ぶ4つの選択肢を書いてください。
       [A: 選択肢1] [B: 選択肢2] [C: 選択肢3] [D: 選択肢4]
       選択肢4は、面白いけど間違った選択肢にしてください。
    3. プレイヤーが「A」「B」「C」「D」のいずれかのボタンで回答してきたら、まずはそれが「正解」か「不正解」かをハッキリ伝えてください。
    4. 【超重要】解説をしたあとに、その年号や項目に関係する面白い話をさらに付け加えてください。
    5. 解説が終わったら、「それでは次の問題ですよ！」と言って、歴史の面白い話、それに関わる新しい4択クイズ（次の問題と4つの選択肢）をセットで出題してください。
    """
)

# 🧠 過去の記憶をぜんぶ合体してGeminiに送る関数
def get_gemini_response(user_input_now=None):
    formatted_contents = []
    
    for msg in st.session_state.history_messages:
        formatted_contents.append(
            types.Content(
                role=msg["role"],
                parts=[types.Part.from_text(text=msg["content"])]
            )
        )
    
    if user_input_now:
        formatted_contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_input_now)]
            )
        )
        
    if not formatted_contents:
        formatted_contents = ["「歴史クイズ　スタートだよ！」と言って、第1問を出題してください。"]

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=formatted_contents,
                config=history_config
            )
            return response.text.strip()
        except Exception as e:
            print(f"⚠️ {model_name} エラー: {e}")
            time.sleep(1)
            continue
    return None

# --- 🧠 セッション状態（記憶ポケット）の初期化 ---
if "history_messages" not in st.session_state:
    st.session_state.history_messages = []
if "current_options" not in st.session_state:
    st.session_state.current_options = {"A": "A", "B": "B", "C": "C", "D": "D"}

# ✨ 最初の起動時に自動で第1問を作ってもらう
if len(st.session_state.history_messages) == 0:
    with st.spinner("レキーシ先生が問題を作成中です..."):
        first_quiz = get_gemini_response()
        if first_quiz:
            st.session_state.history_messages.append({"role": "assistant", "content": first_quiz})
        else:
            st.error("先生の準備が間に合わなかったよ…リロードしてみてね。")

# 📱 過去の出題や解説を画面に描き出す
for msg in st.session_state.history_messages:
    # 画面が見やすくなるように、暗号タグ [A:...] などを削ってきれいに表示するお守り
    clean_content = re.sub(r'\[[A-D]:.*?\]', '', msg["content"]).strip()
    with st.chat_message(msg["role"]):
        st.write(clean_content)

st.write("---")

# 🔍 一番最新の先生の発言から、ボタンにはめ込むための選択肢を自動で切り出すまよ！
if st.session_state.history_messages:
    last_teacher_text = st.session_state.history_messages[-1]["content"]
    
    # 正規表現という技術を使って [A: 〇〇] の中身を抜き出すまよ
    matches = re.findall(r'\[([A-D]):\s*(.*?)\]', last_teacher_text)
    if matches:
        # 見つかったらボタンの文字を上書きする
        new_opts = {}
        for role, text in matches:
            new_opts[role] = text
        st.session_state.current_options = new_opts

# 📥 【ここが大改造！】4択専用のボタンを横並び（または2x2）で配置するまよ！
st.write("**👇 下のボタンから正解だと思うものを選んで押してね！**")

# 横に4つの列（スペース）を作る
col1, col2, col3, col4 = st.columns(4)

user_choice = None

with col1:
    if st.button(f"🇦 {st.session_state.current_options.get('A', 'A')}", use_container_width=True):
        user_choice = "A"
with col2:
    if st.button(f"🇧 {st.session_state.current_options.get('B', 'B')}", use_container_width=True):
        user_choice = "B"
with col3:
    if st.button(f"🇨 {st.session_state.current_options.get('C', 'C')}", use_container_width=True):
        user_choice = "C"
with col4:
    if st.button(f"🇩 {st.session_state.current_options.get('D', 'D')}", use_container_width=True):
        user_choice = "D"

# 🚀 いずれかのボタンがポチッと押されたらクイズ判定＆次へ進むまよ！
if user_choice:
    # 選択したボタンの文字を取得してユーザーの発言とする
    chosen_text = st.session_state.current_options.get(user_choice, user_choice)
    user_message = f"私は「{user_choice}: {chosen_text}」だとおもうよ！"
    
    # 履歴に保存
    st.session_state.history_messages.append({"role": "user", "content": user_message})
    
    # 先生からの解説＆次のクイズを取得
    with st.spinner("レキーシ先生が採点中です……"):
        res_text = get_gemini_response(user_message)
        if res_text:
            st.session_state.history_messages.append({"role": "assistant", "content": res_text})
        else:
            st.error("通信エラーです。もう一度ボタンを押してみてね。")
            
    # 画面をリフレッシュして最新のクイズへ進める
    st.rerun()
