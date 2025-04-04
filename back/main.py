from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import sqlite3
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from collections import Counter
#pyvis
from pyvis.network import Network


app = FastAPI()

#fastapi アクセス認証（ここからのアクセスならOK）
app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:8080"],  # Vue.jsのURLを指定
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

#DB情報
dbname = "Llama3.db"

table_object = "object"
table_method = "method"
table_dataset = "dataset"
table_cluster = "cluster" #dataset=1-142, method=143-301, objective=302-819 (クラスタ番号)

three_pair = "three_pair"
object_method = "ob_mt_pair"
object_dataset = "ob_da_pair"
method_dataset = "mt_da_pair"

three_num = "three_cls_num"
ob_mt_num = "ob_mt_num"
ob_da_num = "ob_da_num"
mt_da_num = "mt_da_num"

#定義
class UserItem(BaseModel):
  input_object: str

#DB接続
def db_conect():
  with sqlite3.connect(dbname) as conn:
    return conn
    
#model準備
def model_prepare():
  return SentenceTransformer("sentence-transformers/paraphrase-distilroberta-base-v1")
    
#クエリ処理
def search_faq(query, model, index, k):
  query_embedding = model.encode([query]) #質問文をベクトル化
  distances, indices = index.search(np.array(query_embedding), k) #Faissデータベースから類似している文のトップ3を取得．kはトップkまで取得する意味
  return indices[0]

#結果の取得
def get_faq_results(faq_id): #id 1つ
  conn = db_conect()
  cur = conn.cursor()
  row = cur.execute(f"SELECT name FROM object WHERE id={faq_id}").fetchone() #結果をデータベースから取得　（課題)
  cls_num = cur.execute(f"SELECT cls_num FROM {table_cluster} WHERE name='{row[0]}'").fetchone() #クラスタ番号を取得
  pair_nums = cur.execute(f"SELECT num1,num2 FROM {three_num} WHERE num1={cls_num[0]} OR num2={cls_num[0]}").fetchall() #pairとなっているitemを取得

  pair_num = [x if x != cls_num[0] else y for x, y in pair_nums]
  dataset_ls = [x for x in pair_num if 1<= x <=142]
  method_ls = [x for x in pair_num if 143<= x <=301]
  pair_num.append(cls_num[0])
  return pair_num, dataset_ls, method_ls, cls_num[0]

#辞書作成
def make_dic():
  conn = db_conect()
  cur = conn.cursor()
  cls_dict={}
  cls_make = cur.execute(f"SELECT name,cls_num FROM {table_cluster}").fetchall()

  for data_name, cluster_id in cls_make:
      if cluster_id not in cls_dict:
          cls_dict[cluster_id] = []
      cls_dict[cluster_id].append(data_name)
    
  most_count = {} #最頻値のitemを代表値とする
  for cluster_id, data_names in cls_dict.items():
      counter = Counter(data_names)
      most_common_name = counter.most_common(1)[0][0]
      most_count[cluster_id] = most_common_name
  return most_count

#pyvisグラフ作成
def create_graph(ls, search_num, cluster_dict):
  net_path = "pyvis.html"
  net = Network(notebook=True, cdn_resources='remote')

  conn = db_conect()
  cur = conn.cursor()
  rows = cur.execute(f"SELECT * FROM {three_num} WHERE num1 IN ({','.join(['?']*len(ls))}) OR num2 IN ({','.join(['?']*len(ls))})", ls + ls)
  for row in rows:
      if row[1] == search_num:
          net.add_node(row[1], label=cluster_dict[row[1]], color="rgb(239, 78, 78)")
          net.add_node(row[2], label=cluster_dict[row[2]])
          net.add_edge(row[1], row[2], color="rgb(90, 196, 246)")
      elif row[2] == search_num:
          net.add_node(row[1], label=cluster_dict[row[1]])
          net.add_node(row[2], label=cluster_dict[row[2]], color="rgb(239, 78, 78)")
          net.add_edge(row[1], row[2], color="rgb(90, 196, 246)")
      elif row[3] > 1:
          net.add_node(row[1], label=cluster_dict[row[1]])
          net.add_node(row[2], label=cluster_dict[row[2]])
          net.add_edge(row[1], row[2], color="rgb(90, 196, 246)")

  net.show(net_path)
  return net_path

#Route
@app.post("/items")
def search_object(item: UserItem):
    model = model_prepare()
    loaded_index = faiss.read_index("index_file.index") #index読み込み
    k = 1 #クラスタ番号を使うため１つだけ
    indice = search_faq(item.input_object, model, loaded_index, k) #1つだけ
    new_indice = int(indice[0])
    
    pair_num, dataset_list, method_list, search_num = get_faq_results(new_indice)

    cluster_dict = make_dic() #クラスタ辞書

    dataset_text = [cluster_dict[x] for x in dataset_list]
    method_text = [cluster_dict[x] for x in method_list]
    return JSONResponse(content={"method": method_text, "dataset": dataset_text})

@app.post("/graph")
def create_pyvis(item: UserItem):
    model = model_prepare()
    loaded_index = faiss.read_index("index_file.index") #index読み込み
    k = 1 #クラスタ番号を使うため１つだけ
    indice = search_faq(item.input_object, model, loaded_index, k) #1つだけ
    new_indice = int(indice[0])
    
    pair_num, dataset_list, method_list, search_num = get_faq_results(new_indice)

    cluster_dict = make_dic() #クラスタ辞書
    net_path = create_graph(pair_num, search_num, cluster_dict) #グラフ作成
    return FileResponse(net_path, media_type="text/html")