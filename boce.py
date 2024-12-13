import requests
import json
import time

class Main(object):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.tg_bot ="" #botfather token
        self.tg_chat ="" #telegram chat id
        self.text=""
        self.boce_key ="" #boce key
        self.domains ="" #用逗号隔开需要检测的域名
        self.domains_array =self.domains.split(',')
        self.node_id =""
        self.task_id =""
        self.boce_wall_code={0:'正常',1:'被墙',2:'疑似被墙',3:'无资源'}

    def check_node(self,key):   
        return requests.post(f'https://api.boce.com/v3/node/list?key={key}')

    def check_wall(self,key,domain):
        #10波点/节点/次
        return requests.post(f'https://api.boce.com/v3/task/create/wall?key={key}&host={domain}')

    def create_hijack(self,key,node,domain):
        return requests.post(f'https://api.boce.com/v3/task/create/hijack?key={key}&node_ids={node}&host={domain}') 
    
    def check_hijack(self,key,task):
        #10波点/域名/次
        return requests.post(f'https://api.boce.com/v3/task/hijack/{task}?key={key}') 
    
    def send_tg(self,bot,chat,text):
        return requests.post(f'https://api.telegram.org/bot{bot}/sendMessage?chat_id={chat}&text={text}&parse_mode=html')

    def run(self):

        #检查所有国内的节点列表
        boce_nodes = self.check_node(key=self.boce_key)
        if boce_nodes.status_code == requests.codes.ok:
                node_datas = json.loads(boce_nodes.text)
                if node_datas.get('error'):
                    self.send_tg(bot=self.tg_bot, chat=self.tg_chat, text=f"返回错误: {node_datas['error']}") 

                node_details=node_datas['data'].get('list',{})
                for node in node_details:
                    if node['isp_name'] != '海外':
                        self.node_id = self.node_id +f"{node['id']},"

        time.sleep(3)

        #检查被墙域名
        boce_wall = self.check_wall(key=self.boce_key,domain=self.domains)
        if boce_wall.status_code == requests.codes.ok:
            boce_wall_datas =json.loads(boce_wall.text)

            if boce_wall_datas.get('error'):
                self.send_tg(bot=self.tg_bot, chat=self.tg_chat, text=f"返回错误: {boce_hijack_datas['error']}") 

            for domain in self.domains_array:
                boce_wall_details = boce_wall_datas.get('data','')
                code = boce_wall_details[domain]
                self.text=""
                self.text=self.text +f"{domain}被墙情况: {self.boce_wall_code[code]}\n"
                self.send_tg(bot=self.tg_bot,chat=self.tg_chat,text=self.text)

        self.text=""
        time.sleep(3)

        #检查劫持域名
        for domain in self.domains_array:
            boce_hijack = self.create_hijack(key=self.boce_key, node=self.node_id, domain=domain)
            if boce_hijack.status_code == requests.codes.ok:
                boce_hijack_datas = json.loads(boce_hijack.text)
                
                if boce_hijack_datas.get('error'):
                    self.send_tg(bot=self.tg_bot, chat=self.tg_chat, text=f"返回错误: {boce_hijack_datas['error']}")
                    continue 
                
                self.task_id = boce_hijack_datas['data']['id']
                
                is_done = False
                while not is_done:
                    check_hijack = self.check_hijack(key=self.boce_key, task=self.task_id)
                    check_hijack_datas = json.loads(check_hijack.text)
                    
                    is_done = check_hijack_datas.get('done', False)
                    
                    if is_done:
                        hijack_domain_details = check_hijack_datas.get('list', [])
                        for hijack_domain in hijack_domain_details:
                            if hijack_domain.get('hijack', False):
                                self.text = (
                                    f"{hijack_domain.get('url')}\n\n"
                                    f"{hijack_domain.get('node_name')} 挟持情况: {hijack_domain.get('hijack')}\n"
                                )
                                self.send_tg(bot=self.tg_bot, chat=self.tg_chat, text=self.text)
                            else:
                                self.send_tg(bot=self.tg_bot, chat=self.tg_chat, text=f"{domain}在{hijack_domain.get('node_name')}劫持情况正常")
                        break
                    
                    time.sleep(3)
            else:
                self.send_tg(bot=self.tg_bot, chat=self.tg_chat, text="无法创建挟持任务，请检查请求")

if __name__ == '__main__':
    Main().run()
