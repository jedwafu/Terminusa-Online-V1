<?php
if(!defined('IN_GAME')) {
	exit('Access Denied');
}



function use_func_item($usemode,$item)
{
	if ($usemode=="poison"){poison($item);}
	elseif ($usemode=="wthchange"){wthchange($item);}
	elseif ($usemode=="hack") {hack($item);}
	elseif ($usemode=="newradar") {newradar($item);}
	elseif ($usemode=="divining") {divining($item);}
	elseif ($usemode=="divining1") {divining1($item);}
	elseif ($usemode=="divining2") {divining2($item);}
	elseif ($usemode=="deathnote") {deathnote($item);}
	elseif ($usemode=="qianghua") {qianghua($item);}
	elseif ($usemode=="nametag") {nametag($item);}
	elseif ($usemode=="supernametag") {supernametag($item);}
}

function poison($itmn = 0) {
	global $mode,$log,$nosta,$art,$club,$pid;
	global $itmp,${'itm'.$itmp},${'itms'.$itmp},${'itmk'.$itmp},${'itme'.$itmp},${'itmsk'.$itmp}, ${'itmpara'. $itmp};
	$poison = & ${'itm'.$itmp};
	$poisonk = & ${'itmk'.$itmp};
	$poisone = & ${'itme'.$itmp};
	$poisons = & ${'itms'.$itmp};
	$poisonsk = & ${'itmsk'.$itmp};
	$poisonpara = & ${'itmpara'. $itmp};
	if ( $itmn < 1 || $itmn > 6 ) {
		$log .= '此道具不存在，请重新选择。';
		$mode = 'command';
		return;
	}
	global ${'itm'.$itmn},${'itmk'.$itmn},${'itmsk'.$itmn}, ${'itmpara'. $itmn};
	$itm = & ${'itm'.$itmn};
	$itmk = & ${'itmk'.$itmn};
	$itmsk = & ${'itmsk'.$itmn};
	$itmpara = & ${'itmpara'. $itmn};
	if(($poison != '毒药') || (strpos($itmk, 'H') !==0 && strpos($itmk, 'P') !== 0)) {
		$log .= '道具选择错误，请重新选择。<br>';
		$mode = 'command';
		return;
	}
	$itmk = substr_replace($itmk,'P',0,1);
	if($club == 8){ $itmk = substr_replace($itmk,'2',2,1); }
	elseif($art == '毒物说明书'){$itmk = substr_replace($itmk,'1',2,1);};
	if($art == '妖精的羽翼') {$itmk = substr_replace($itmk,'H',0,1);$log .= "一种神秘的力量净化了毒药，你的毒药变成了解毒剂！";}
	$itmsk = $pid;
	if($art == '妖精的羽翼') {$log .= "使用了 <span class=\"red\">$poison</span> ，<span class=\"yellow\">{${'itm'.$itmn}}</span> 被净化了！<br>";}
	else {$log .= "使用了 <span class=\"red\">$poison</span> ，<span class=\"yellow\">{${'itm'.$itmn}}</span> 被下毒了！<br>";}
	$poisons--;
	if($poisons <= 0){
		$log .= "<span class=\"red\">$poison</span> 用光了。<br>";
		$poison = $poisonk = '';$poisone = $poisons = 0;
	}


	$mode = 'command';
	return;
}

function wthchange($itm,$itmsk,$wlog=1){
	global $now,$log,$weather,$wthinfo,$name,$nick,$clbpara;
	$weathertd = $weather;
	if($weather >= 14 && $weather <= 18){
		addnews ( $now, 'wthfail',$name, $weather, $itm , $nick);
		$log .= "你使用了{$itm}。<br /><span class=\"red\">但是天气并未发生任何变化！</span><br />";
	}else{
		if($itmsk==99){$weather = rand ( 0, 13 );}//随机全天气
		elseif($itmsk==98){$weather = rand ( 10, 13 );}//随机恶劣天气
		elseif($itmsk==97){$weather = rand ( 0, 9 );}//随机一般天气
		elseif($itmsk==96){$weather = rand ( 8, 9 );}//随机起雾天气
		elseif($itmsk==95){$weather = 17;}//极光天气
		elseif(!empty($itmsk) && is_numeric($itmsk)){
			if($itmsk >=0 && $itmsk < count($wthinfo)){
				$weather = $itmsk;
			}else{$weather = 0;}
		}
		else{$weather = 0;}
		
		$flag = false;
		if($itm=='【风神的神德】'){
			//$dice = rand ( 1, 18 );
			$dice = rand ( 1, 30 );
			if ($dice < 18){
				$flag = true;
			} else{
				$weather = 6;
			}
		}
		if($flag){
			global $hp;
			$weather = $weathertd;
			$log .= "你使用了<span class=\"yellow\">{$itm}</span>。<br>“好像没什么反应嘛？”";
			//include_once GAME_ROOT . './include/state.func.php';
			//$log .= "你正这样想着，天空中忽然传来一阵巨响！”<br>“祈求神德的话，就以你的生命作为祭品吧！<br>你只来得及看到一个巨大的柱状物飞来，就失去了意识。";
			//death ( 'thunde', '', 0, $itm );
			$log .= "你正这样想着，天空中忽然传来一阵巨响！”<br>“祈求神德的话，就以你的生命作为祭品吧！<br>你只来得及看到一个巨大的柱状物飞来，便觉得眼前一黑！<br>";
			$log .= "<span class = \"damage\">你受到了巨大的伤害！</span>";
			$hp = 9;
		} else {
			include_once GAME_ROOT . './include/system.func.php';
			save_gameinfo ();
			addnews ( $now, 'wthchange', $name, $weather, $itm , $nick);
			if($wlog) $log .= "你使用了<span class=\"yellow\">{$itm}</span>。<br />天气突然转变成了<span class=\"red\">$wthinfo[$weather]</span>！<br />";
		}
		$clbpara['achvars']['wthchange'] += 1;
	}
	return;
}

function hack($itmn = 0) {
	global $log,$hack,$hack_obbs,$club,$clbpara,$now,$name,$alivenum,$deathnum,$hp,$state,$nick;
	
	global ${'itm'.$itmn},${'itmk'.$itmn},${'itme'.$itmn},${'itms'.$itmn},${'itmsk'.$itmn}, ${'itmpara'. $itmn};
	$itm = & ${'itm'.$itmn};
	$itmk = & ${'itmk'.$itmn};
	$itme = & ${'itme'.$itmn};
	$itms = & ${'itms'.$itmn};
	$itmsk = & ${'itmsk'.$itmn};
	$itmpara = & ${'itmpara'. $itmn};


	if(!$itms) {
		$log .= '此道具不存在，请重新选择。<br>';
		$mode = 'command';
		return;
	}

	if(!$itme) {
		$log .= "<span class=\"yellow\">$itm</span>已经没电，请寻找<span class=\"yellow\">电池</span>充电。<br>";
		$mode = 'command';
		return;
	}

	$hack_dice = rand(0,99);
	if(($hack_dice < $hack_obbs)||(($club == 7)&&($hack_dice<95))) {
		$hack = 1;
		$clbpara['achvars']['hack'] += 1;
		$log .= '入侵禁区控制系统成功了！全部禁区都被解除了！<br>';
		//include_once GAME_ROOT.'./include/system.func.php';
		//movehtm();
		addnews($now,'hack',$name,$nick);
		storyputchat($now,'hack');
		save_gameinfo();
	} else {
		$log .= '可是，入侵禁区控制系统失败了……<br>';
	}
	if($club == 7){
		$e_dice = rand(0,1);
		if($e_dice == 1){
			$itme--;
			$log .= "消耗了<span class=\"yellow\">$itm</span>的电力。<br>";
		}else{
			$log .= "由于操作迅速，<span class=\"yellow\">$itm</span>的电力没有消耗。<br>";
		}
	}else{
		$itme--;
		$log .= "消耗了<span class=\"yellow\">$itm</span>的电力。<br>";
	}
	
	$hack_dice2 = rand(0,99);

	if($hack_dice2 < 5 && $club != 7) {
		$log .= '由于你的不当操作，禁区系统防火墙锁定了你的电脑并远程引爆了它。幸好你本人的位置并没有被发现。<br>';
		$itm = $itmk = $itmsk = '';
		$itme = $itms = 0;
	} elseif($hack_dice2 < 8 && $club != 7) {
			$log .= "<span class=\"evergreen\">“小心隔墙有耳哦。”</span>——林无月<br>";
			include_once GAME_ROOT.'./include/state.func.php';
			$log .= '你擅自入侵禁区控制系统，被控制系统远程消灭！<br>';
			death('hack');
	} elseif($itme <= 0) {
		$log .= "<span class=\"red\">$itm</span>的电池耗尽了。";
	}
	return;
}

function newradar($m = 0){
	global $mode,$log,$cmd,$main,$pls,$db,$tablepre,$plsinfo,$arealist,$areanum,$hack,$gamestate;
	global $pnum,$npc2num,$npc3num,$npc4num,$npc5num,$npc6num,$radarscreen,$typeinfo,$weather;
	global $horizon;
	
	if((CURSCRIPT !== 'botservice') && (!$mode)) {
		$log .= '仪器使用失败！<br>';
		return;
	}
	//echo $weather;
	if($weather == 14){
		$dice = rand(0,1);
		if($dice == 1){
			$log .= '由于<span class="linen">离子风暴</span>造成了电磁干扰，探测仪器完全显示不出信息……<br>';
			return;
		}
	}

	if($horizon == 1) 
	{
		$npctplist = Array(92,89);
	}
	else
	{
		$npctplist = Array(90,2,5,6,11,14);
	}
	$tdheight = 20;
	$screenheight = count($plsinfo)*$tdheight;
	if (CURSCRIPT == 'botservice') 
	{
		if ($m==2)
			$result = $db->query("SELECT type,sNo,pls,name FROM {$tablepre}players WHERE hp>0");
		else  $result = $db->query("SELECT type,sNo,pls,name FROM {$tablepre}players WHERE hp>0 AND pls='{$pls}'");
		$rows=$db->num_rows($result);
		echo "radarresultnum=$rows\n";
		$i=0;
		while($data = $db->fetch_array($result)) 
		{
			$i++;
			echo "radarresulttype$i={$data['type']}\n";
			echo "radarresultsNo$i={$data['sNo']}\n";
			echo "radarresultpls$i={$data['pls']}\n";
			echo "radarresultname$i={$data['name']}\n";
		}	
	}
	else
	{
		$result = $db->query("SELECT type,pls FROM {$tablepre}players WHERE hp>0");
		while($cd = $db->fetch_array($result)) {
			$chdata[] = $cd;
		}
		$radar = array();
		foreach ($chdata as $data){
			if(isset($radar[$data['pls']][$data['type']])){$radar[$data['pls']][$data['type']]+=1;}
			else{$radar[$data['pls']][$data['type']]=1;}
		}
		$radarscreen = '<table height='.$screenheight.'px width=720px border="0" cellspacing="0" cellpadding="0" valign="middle"><tbody>';
		$radarscreen .= "<tr>
			<td class=b2 height={$tdheight}px width=120px><div class=nttx></div></td>
			<td class=b2><div class=nttx>{$typeinfo[0]}</div></td>";
		foreach ($npctplist as $value){
			$radarscreen .= "<td class=b2><div class=nttx>{$typeinfo[$value]}</div></td>";
		}
		$radarscreen .= '</tr>';
		for($i=0;$i<count($plsinfo);$i++) {
			$radarscreen .= "<tr><td class=b2 height={$tdheight}px><div class=nttx>{$plsinfo[$i]}</div></td>";
			if((array_search($i,$arealist) > $areanum) || $hack) {
				if($i==$pls) {
					//$result = $db->query("SELECT pid FROM {$tablepre}players WHERE hp>0 AND type='0' AND pls=$i");
					//$num0 = $db->num_rows($result);
					$num0 = $radar[$i][0];
					foreach ($npctplist as $j){
						//$result = $db->query("SELECT pid FROM {$tablepre}players WHERE hp>0 AND type=$j AND pls=$i");
						//${'num'.$j} = $db->num_rows($result);
							if($gamestate == 50){${'num'.$j} = 0;}
						else{
							${'num'.$j} = isset($radar[$i][$j]) ? $radar[$i][$j] : 0;
						}
					}
					if($num0){
						$pnum[$i] ="<span class=\"yellow b\">$num0</span>";
					} else {
						$pnum[$i] ='<span class="yellow b">-</span>';
					}
					foreach ($npctplist as $j){
						//${'npc'.$j.'num'}[$i] = "<span class=\"yellow b\">${'num'.$j}</span>";
						if(${'num'.$j}){
						${'npc'.$j.'num'}[$i] ="<span class=\"yellow b\">{${'num'.$j}}</span>";
						} else {
						${'npc'.$j.'num'}[$i] ='<span class="yellow b">-</span>';
						}
					}
				} elseif($m >= 2) {
					//$result = $db->query("SELECT pid FROM {$tablepre}players WHERE hp>0 AND type='0' AND pls=$i");
					//$num0 = $db->num_rows($result);
					$num0 = isset($radar[$i][0]) ? $radar[$i][0] : 0;
					foreach ($npctplist as $j){
						//$result = $db->query("SELECT pid FROM {$tablepre}players WHERE hp>0 AND type=$j AND pls=$i");
						//${'num'.$j} = $db->num_rows($result);
						if($gamestate == 50){${'num'.$j} = 0;}
						else{
							${'num'.$j} = isset($radar[$i][$j]) ? $radar[$i][$j] : 0;
						}
						
					}
					if ($m==2)
						if($num0){
							$pnum[$i] =$num0;
						} else {
							$pnum[$i] ='-';
						}	
					else  $pnum[$i] = '？';
					//$pnum[$i] ="$num0";
					foreach ($npctplist as $j){
						//${'npc'.$j.'num'}[$i] = "${'num'.$j}";;
						if(${'num'.$j}){
	
							${'npc'.$j.'num'}[$i] =${'num'.$j};

						} else {
							${'npc'.$j.'num'}[$i] ='-';
						}
					}
				} else {
					$pnum[$i] = '？';
					foreach ($npctplist as $j){
						${'npc'.$j.'num'}[$i] = '？';
					}
				}	
			} else {	
				$pnum[$i] = '<span class="red b">×</span>';
				foreach ($npctplist as $j){
				${'npc'.$j.'num'}[$i] = '<span class="red b">×</span>';
				}
			}
			$radarscreen .= "<td class=b3><div class=nttx>{$pnum[$i]}</div></td>";
			foreach ($npctplist as $j){
				$radarscreen .= "<td class=b3><div class=nttx>{${'npc'.$j.'num'}[$i]}</div></td>";
			}	
			$radarscreen .= '</tr>';
		}
		$radarscreen .= '</tbody></table>';
		$log .= '白色数字：该区域内的人数<br><span class="yellow">黄色数字</span>：自己所在区域的人数<br><span class="red b">×</span>：禁区<br><br>';
		include template('radarcmd');
		$cmd = ob_get_contents();
		ob_clean();
		//$cmd = '<input type="radio" name="command" id="menu" value="menu" checked><a onclick=sl("menu"); href="javascript:void(0);" >返回</a><br><br>';
		$main = 'radar';
	}
	return;
}

function divining(){
	global $log;
	
	$dice = rand(0,99);
	if($dice < 20) {
		$up = 5;
		list($uphp,$upatt,$updef) = explode(',',divining1($up));
		$log .= "是大吉！要有什么好事发生了！<BR><span class=\"yellow b\">【命】+$uphp 【攻】+$upatt 【防】+$updef</span><BR>";
	} elseif($dice < 40) {
		$up = 3;
		list($uphp,$upatt,$updef) = explode(',',divining1($up));
		$log .= "中吉吗？感觉还不错！<BR><span class=\"yellow b\">【命】+$uphp 【攻】+$upatt 【防】+$updef</span><BR>";
	} elseif($dice < 60) {
		$up = 1;
		list($uphp,$upatt,$updef) = explode(',',divining1($up));
		$log .= "小吉吗？有跟无也没有什么分别。<BR><span class=\"yellow b\">【命】+$uphp 【攻】+$upatt 【防】+$updef</span><BR>";
	} elseif($dice < 80) {
		$up = 1;
		list($uphp,$upatt,$updef) = explode(',',divining2($up));
		$log .= "凶，真是不吉利。<BR><span class=\"red b\">【命】-$uphp 【攻】-$upatt 【防】-$updef</span><BR>";
	} else {
		$up = 3;
		list($uphp,$upatt,$updef) = explode(',',divining2($up));
		$log .= "大凶？总觉得有什么可怕的事快要发生了<BR><span class=\"red b\">【命】-$uphp 【攻】-$upatt 【防】-$updef</span><BR>";
	}
	return;
}

function divining1($u) {
	global $hp,$mhp,$att,$def;
	$uphp = rand(0,$u);
	$upatt = rand(0,$u);
	$updef = rand(0,$u);
	
	$hp+=$uphp;
	$mhp+=$uphp;
	$att+=$upatt;
	$def+=$updef;
	
	
	return "$uphp,$upatt,$updef";

}

function divining2($u) {
	global $hp,$mhp,$att,$def;
	$uphp = rand(0,$u);
	$upatt = rand(0,$u);
	$updef = rand(0,$u);
	
	if($hp - $uphp <= 0){
		$uphp = $hp-1;
		if($uphp < 0){$uphp = 0;}
	}
	
	$hp-=$uphp;
	$mhp-=$uphp;
	$att-=$upatt;
	$def-=$updef;
	
	return "$uphp,$upatt,$updef";
}

function deathnote($sfn,$itmd=0,$dnname='',$dndeath='',$dngender='m',$dnicon=1) {
	global $db,$tablepre,$log,$killnum,$mode,$achievement,$pdata;
	global ${'itm'.$itmd},${'itms'.$itmd},${'itmk'.$itmd},${'itme'.$itmd},${'itmsk'.$itmd},${'itmpara'. $itmd};
	$dn = & ${'itm'.$itmd};
	$dnk = & ${'itmk'.$itmd};
	$dne = & ${'itme'.$itmd};
	$dns = & ${'itms'.$itmd};
	$dnsk = & ${'itmsk'.$itmd};
	$dnpara = & ${'itmpara'. $itmd};

	$mode = 'command';

	if($dn != '■DeathNote■' && $dn != '四面亲手制作的■DeathNote■' ){
		$log .= '道具使用错误！<br>';
		return;
	} elseif($dns <= 0) {
		$dn = $dnk = $dnsk = $dnpara = '';
		$dne = $dns = 0;
		$log .= '道具不存在！<br>';
		return;
	}

	if(!$dnname){return;}
	if($dnname == $sfn && $dn != '四面亲手制作的■DeathNote■'){
		$log .= "你不能自杀。<br>";
		return;
	}
	if(!$dndeath){$dndeath = '心脏麻痹';}
	if ($dn == '四面亲手制作的■DeathNote■') $dndeath="使用了天然呆四面的假冒伪劣■DeathNote■";
	//echo "name=$dnname,gender = $dngender,icon=$dnicon,";
	if ($dn != '四面亲手制作的■DeathNote■') 
		$result = $db->query("SELECT * FROM {$tablepre}players WHERE name='$dnname' AND type = 0");
	else  $result = $db->query("SELECT * FROM {$tablepre}players WHERE name='$sfn' AND type = 0");
	if(!$db->num_rows($result)) { 
		$log .= "你使用了■DeathNote■，但是什么都没有发生。<br>哪里出错了？<br>"; 
	} else {
		$edata = $db->fetch_array($result);
		
		if((($dngender != $edata['gd'])||($dnicon != $edata['icon'])) && ($dn != '四面亲手制作的■DeathNote■')) {
			$log .= "你使用了■DeathNote■，但是什么都没有发生。<br>哪里出错了？<br>"; 
		} else {
			if ($dn != '四面亲手制作的■DeathNote■') 
			{
				$log .= "你将<span class=\"yellow b\">$dnname</span>的名字写在了■DeathNote■上。<br>";
				$log .= "<span class=\"yellow b\">$dnname</span>被你杀死了。";
				//include_once GAME_ROOT.'./include/state.func.php';
				//kill('dn',$dnname,0,$edata['pid'],$dndeath);
				//$killnum++;
				$pdata['wep_name'] = $dndeath;
				include_once GAME_ROOT.'./include/state.func.php';
				pre_kill_events($pdata,$edata,1,'dn');
				// 如果希望被DN后能够复活，可以在这里调用一次复活判定函数
				final_kill_events($pdata,$edata,1);
				player_save($edata);
			}
			else  
			{
				$log .= "你将<span class=\"yellow b\">$dnname</span>的名字写在了■DeathNote■上。<br>";
				$log .= "但就在这时，你突然感觉一阵晕眩。<br>你失去了意识。<br>";
				$log .= "<span class='lime'>“这张■DeathNote■似乎制作不合格呢，还真是对不起呢……”<br></span>";
				include_once GAME_ROOT.'./include/state.func.php';
				death ( 'fake_dn', '', 0, $dndeath);
				$killnum++;
			}
		}
	}
	$dns--;
	if($dns<=0){
		$log .= '■DeathNote■突然燃烧起来，转瞬间化成了灰烬。<br>';
		$dn = $dnk = $dnsk = $dnpara = '';
		$dne = $dns = 0;
	}
	return;
}

function qianghua($itmn = 0) {
	global $mode,$log,$nosta,$name,$nick;
	global $club;
	global $itmp,${'itm'.$itmp},${'itms'.$itmp},${'itmk'.$itmp},${'itme'.$itmp},${'itmsk'.$itmp}, ${'itmpara'. $itmp};
	$baoshi = & ${'itm'.$itmp};
	$baoshie = & ${'itme'.$itmp};
	$baoshis = & ${'itms'.$itmp};
	$baoshik = & ${'itmk'.$itmp};
	$baoshisk = & ${'itmsk'.$itmp};	
	$baoshipara = & ${'itmpara'. $itmp};
	if ( $itmn < 1 || $itmn > 6 ) {
		$log .= '此道具不存在，请重新选择。';
		$mode = 'command';
		return;
	}
	global ${'itm'.$itmn},${'itme'.$itmn},${'itms'.$itmn},${'itmk'.$itmn},${'itmsk'.$itmn}, ${'itmpara'. $itmn};
	$itm = & ${'itm'.$itmn};
	$itme = & ${'itme'.$itmn};
	$itms = & ${'itms'.$itmn};
	$itmk = & ${'itmk'.$itmn};
	$itmsk = & ${'itmsk'.$itmn};
	$itmpara = & ${'itmpara'. $itmn};
	if($baoshis <= 0 || ($baoshi != '『灵魂宝石』' && $baoshi != '『祝福宝石』')) {
		$log .= '强化道具选择错误，请重新选择。<br>';
		$mode = 'command';
		return;
	}
	if(!$itms || strpos ( $itmsk, 'Z' ) === false) {
		$log .= '被强化道具选择错误，请重新选择。<br>';
		$mode = 'command';
		return;
	}
		# Detect if club 21, if so, output easter egg and return.
	if ($club == 21){
		$log .= "<span class=\"yellow\">突然，你的眼前出现了扭曲的字符！</span><br>";
		$log .= "<span class=\"glitchb\">
		“纠结纠结小问号，<br>
		代码溢出怎么搞？<br>
		干脆一刀禁了它。
		反正挨打不用愁！<br>”</span><br>";
		$log .= "<span class=\"yellow\">唔，看起来这个宝石对你似乎没有什么意义……</span><br>";
		$mode = 'command';
		return;
		}
	$o_itm = $itm;
	if(!preg_match("/\[\+[0-9]\]/",$itm)){
		$itm = ${'itm'.$itmn}.'[+0]';
//		$itme = round(${'itme'.$itmn} * 1.5);
		$flag = true;
		$zitmlv = 0;
//		var_dump($zitmlv);
	}else{
		//$zitmlv = preg_replace("/\[\+([0-9])\]/","\\1",$zitmlv[0]);
		preg_match("/\[\+([0-9])\]/",$itm,$zitmlv);
		//var_dump($zitmlv);
		$zitmlv = $zitmlv[1];
		//$dengji = substr(${'itm'.$itmn},strpos(${'itm'.$itmn},"[+")+2,strlen(${'itm'.$itmn}) - strpos(${'itm'.$itmn},"]")+1);//北京你自己看着办
    //$dengji = str_replace(']','',$dengji);
		if($zitmlv >= 4 && $baoshi != '『灵魂宝石』'){
			$log .= '你所选的宝石只能强化装备到[+4]哦!DA☆ZE<br>';
		  $mode = 'command';
			return;
		}else{
			if ($zitmlv==3 && $baoshi=='『祝福宝石』'){ 
				if ($baoshis<2)
				{
					$log .= '你需要至少2颗祝福宝石才能强化装备到[+4]哦!DA☆ZE<br>';
					$mode = 'command';
					return;
				}
				elseif ($baoshis==2) 	//两颗成功率1/3
				{
					$baoshis--;
					$dice = rand(1,30);
				}
				else 			//3颗必定成功
				{
					$baoshis -= 2;
					$dice = 1;
				}
			}elseif ($zitmlv >= 4){
				$dice = rand(1,10*($zitmlv-2));//+5概率10/20，+6概率10/30，+7概率10/40，+8概率10/50与原来相同
//				$gailv = rand(1,$zitmlv-2);//原代码因为错误的缘故只能执行这里，概率是1/(当前lv-2)，也即冲+5就是1/2,冲+6就是1/3以此类推
//			}elseif ($zitmlv >= 6){
//				$gailv = rand(1,$zitmlv-1);
//			}elseif ($zitmlv >= 10){
//				$gailv = rand(1,$zitmlv);
			}else{
				$dice = 1;
			}
			if ($dice <= 10 ){
				$flag = true;
			}else{$flag = false;}
	  }	
  }	
  addnews ( $now, 'newwep2',$name, $baoshi, $o_itm , $nick);
	if ($flag){
		# Detect item names that's too long - if so, trigger this easter egg and fix the item name to prevent exploit.
		if(mb_strlen($o_itm,'utf-8')>=30){
			$log .= "<span class=\"yellow\">突然，有另一把声音插了进来！</span><br>";
			$log .= "<span class=\"glitch1\">“我是大魔王昆顿，你们这些中二入脑的英雄们都喜欢将自己的装备名字取得很长，我很生气！<br>就让我毁灭你的中二吧！”</span><br>";

		#搞事！
		$itm = "★破灭的中二之魂★";
		$log .= "<span class=\"yellow\">『你的全身被恐怖感缠绕，只能眼睁睁地看着大魔王将你的中二之魂打成了碎片！<br>但惊异的是，它的性能竟然毫无变化。』</span><br>";
		$log .= "<span class=\"glitch1\">“毕竟老夫也不是什么恶魔嘛——那么我的气消了，凯莉你继续吧。”</span><br>";
		}

	 $log .= "<span class=\"yellow\">『一道神圣的闪光照耀在你的眼睛上，当你恢复视力时，发现你的装备闪耀着彩虹般的光芒』</span><br>";
	 $nzitmlv = $zitmlv +1;
	 $itm = str_replace('[+'.$zitmlv.']','[+'.$nzitmlv.']',$itm);
	 $itme = round($itme * (1.5 + 0.1 * $zitmlv));
	}else{
	 //$ran = rand(5,20);
	 //$log .="<span class=\"yellow\">『一道神圣的闪光照耀在你的眼睛上，当你恢复视力时，发现你的装备变成了{$ran}块闪耀着彩虹光芒的碎片』</span><br>";
	 //$itm = "★散发着彩虹光芒的的碎片★";
	 $itm = "悲叹之种";
	 //$itme = round(${'itme'.$itmn} / $ran);
	 $itme = 1;
	 //$itms = $ran;
	 $itms = 1;
	 $itmk = 'X';
	 $itmsk = '';
	 $log .="<span class=\"yellow\">『一道神圣的闪光照耀在你的眼睛上，当你恢复视力时，发现你的装备变成了{$itm}』</span><br>";
	}			
	$baoshis--;
	if($baoshis <= 0){
		$log .= "<span class=\"red\">$baoshi</span> 用光了。<br>";
		$baoshi = $baoshik = $baoshisk = $baoshipara = '';$baoshie = $baoshis = 0;
	}	
	$mode = 'command';
	return;
}	

function nametag($item){
	global $rename,$ntitm,$log,$now,$command,$mode,$nosta;
	global ${'itm'.$ntitm},${'itms'.$ntitm},${'itmk'.$ntitm},${'itme'.$ntitm},${'itmsk'.$ntitm}, ${'itmpara'.$ntitm};
	if(${'itm'.$ntitm} != '残响兵器' || ${'itmk'.$ntitm} != 'Y' || !${'itms'.$ntitm}){
		$log .= "<span class=\"yellow\">道具不存在！</span><br>";
		$mode = 'command';
		return;
	}
	if($item == 'itm'.$ntitm){
		$log .= "<span class=\"yellow\">不能修改道具自身！</span><br>";
		$mode = 'command';
		return;
	}
	if(strpos($item,'itm')===0){
		$i = str_replace('itm','',$item);
		global ${'itm'.$i},${'itms'.$i},${'itmk'.$i},${'itme'.$i},${'itmsk'.$i}, ${'itmpara'.$i};
		$rn = & ${'itm'.$i};
		$rnk = & ${'itmk'.$i};
		$rne = & ${'itme'.$i};
		$rns = & ${'itms'.$i};
		$rnsk = & ${'itmsk'.$i};
		$rnpara = & ${'itmpara'.$i};
	}else{
		global ${$item},${$item.'k'}, ${$item.'e'}, ${$item.'s'},${$item.'sk'}, ${$item.'para'};
		$rn = & ${$item};
		$rnk = & ${$item.'k'};
		$rne = & ${$item.'e'};
		$rns = & ${$item.'s'};
		$rnsk = & ${$item.'sk'};
		$rnpara = & ${$item.'para'};
	}
	
	
	if(!$rns || !$rne){
		$log .= "<span class=\"yellow\">道具选择错误！</span><br>";
		$mode = 'command';
		return;
	}
	if(strpos($rnk,'Y')===0 || strpos($rnk,'Z')===0){
		$log .= "<span class=\"yellow\">不能修改特殊道具的名字！</span><br>";
		$mode = 'command';
		return;
	}
	if(!$rename){
		$log .= "<span class=\"yellow\">请输入符合要求的名字！</span><br>";
		$mode = 'command';
		return;
	}
	$mark = '■';
	$rn0 = $rn;
	$rn = $mark.$rename.$mark;
	//Let's add another invisible branding
	$rnsk .= '🔰';
	$rnsk = str_replace('Z','x',$rnsk);
	$log .= "{$rn0}已改名为<span class=\"yellow\">$rn</span>！武器的菁英属性已经抹消。<br>";

	if(${'itms'.$ntitm} != $nosta){
		${'itms'.$ntitm} --;
		if(${'itms'.$ntitm} <= 0){
			$log .= "<span class=\"yellow\">{${'itm'.$ntitm}}用完了。</span><br>";
			${'itm'.$ntitm} = ${'itmk'.$ntitm} = ${'itmsk'.$ntitm} = ${'itmpara'.$ntitm} = '';
			${'itms'.$ntitm} = ${'itme'.$ntitm} = 0;		
		}
	}
	$mode = 'command';
	return;
}
function supernametag($item){
	global $rename,$ntitm,$log,$now,$command,$mode,$nosta;
	global ${'itm'.$ntitm},${'itms'.$ntitm},${'itmk'.$ntitm},${'itme'.$ntitm},${'itmsk'.$ntitm};
	if(${'itm'.$ntitm} != '超臆想时空' || ${'itmk'.$ntitm} != 'Y' || !${'itms'.$ntitm}){
		$log .= "<span class=\"yellow\">道具不存在！</span><br>";
		$mode = 'command';
		return;
	}
	if($item == 'itm'.$ntitm){
		$log .= "<span class=\"yellow\">不能修改道具自身！</span><br>";
		$mode = 'command';
		return;
	}
	if(strpos($item,'itm')===0){
		$i = str_replace('itm','',$item);
		global ${'itm'.$i},${'itms'.$i},${'itmk'.$i},${'itme'.$i},${'itmsk'.$i};
		$rn = & ${'itm'.$i};
		$rnk = & ${'itmk'.$i};
		$rne = & ${'itme'.$i};
		$rns = & ${'itms'.$i};
		$rnsk = & ${'itmsk'.$i};
	}else{
		global ${$item},${$item.'k'}, ${$item.'e'}, ${$item.'s'},${$item.'sk'};
		$rn = & ${$item};
		$rnk = & ${$item.'k'};
		$rne = & ${$item.'e'};
		$rns = & ${$item.'s'};
		$rnsk = & ${$item.'sk'};
	}
	
	
	if(!$rns || !$rne){
		$log .= "<span class=\"yellow\">道具选择错误！</span><br>";
		$mode = 'command';
		return;
	}
	if(strpos($rnk,'Y')===0 || strpos($rnk,'Z')===0){
		$log .= "<span class=\"yellow\">不能修改特殊道具的名字！</span><br>";
		$mode = 'command';
		return;
	}
	if(!$rename){
		$log .= "<span class=\"yellow\">请输入符合要求的名字！</span><br>";
		$mode = 'command';
		return;
	}
	if($rename =='『A.Q.U.A』'){
		$log .= "<span class=\"yellow\">呵呵，你知道的太多了。</span><br>";
		$log .= '你头晕脑胀地躺到了地上，<br>感觉整个人都被救济了。<br>';
		include_once GAME_ROOT . './include/state.func.php';
		$log .= '然后你失去了意识。<br>';
			for ($i=1;$i<=6;$i++){
				global ${'itm'.$i},${'itmk'.$i},${'itme'.$i},${'itms'.$i},${'itmsk'.$i};
				$itm = & ${'itm'.$i};
				$itmk = & ${'itmk'.$i};
				$itme = & ${'itme'.$i};
				$itms = & ${'itms'.$i};
				$itmsk = & ${'itmsk'.$i};
				if ($itm=='黑色发卡') {$flag=true;}
				$itm = '';
				$itmk = '';
				$itme = 0;
				$itms = 0;
				$itmsk = '';
			}
		death ( 'salv', '', 0, $itm );
		//return;	
	}
	if($rename =='『T.E.R.R.A』'){
		$log .= "<span class=\"yellow\">呵呵，你知道的太多了。</span><br>";
		$log .= '你头晕脑胀地躺到了地上，<br>感觉整个人都被救济了。<br>';
		include_once GAME_ROOT . './include/state.func.php';
		$log .= '然后你失去了意识。<br>';
			for ($i=1;$i<=6;$i++){
				global ${'itm'.$i},${'itmk'.$i},${'itme'.$i},${'itms'.$i},${'itmsk'.$i};
				$itm = & ${'itm'.$i};
				$itmk = & ${'itmk'.$i};
				$itme = & ${'itme'.$i};
				$itms = & ${'itms'.$i};
				$itmsk = & ${'itmsk'.$i};
				if ($itm=='黑色发卡') {$flag=true;}
				$itm = '';
				$itmk = '';
				$itme = 0;
				$itms = 0;
				$itmsk = '';
			}
		death ( 'salv', '', 0, $itm );
		//return;	
	}
	if($rename =='『V.E.N.T.U.S』'){
		$log .= "<span class=\"yellow\">呵呵，你知道的太多了。</span><br>";
		$log .= '你头晕脑胀地躺到了地上，<br>感觉整个人都被救济了。<br>';
		include_once GAME_ROOT . './include/state.func.php';
		$log .= '然后你失去了意识。<br>';
			for ($i=1;$i<=6;$i++){
				global ${'itm'.$i},${'itmk'.$i},${'itme'.$i},${'itms'.$i},${'itmsk'.$i};
				$itm = & ${'itm'.$i};
				$itmk = & ${'itmk'.$i};
				$itme = & ${'itme'.$i};
				$itms = & ${'itms'.$i};
				$itmsk = & ${'itmsk'.$i};
				if ($itm=='黑色发卡') {$flag=true;}
				$itm = '';
				$itmk = '';
				$itme = 0;
				$itms = 0;
				$itmsk = '';
			}
		death ( 'salv', '', 0, $itm );
		//return;	
	}
	if($rename =='『C.H.A.O.S』'){
		$log .= "<span class=\"yellow\">呵呵，你知道的太多了。</span><br>";
		$log .= '你头晕脑胀地躺到了地上，<br>感觉整个人都被救济了。<br>';
		include_once GAME_ROOT . './include/state.func.php';
		$log .= '然后你失去了意识。<br>';
			for ($i=1;$i<=6;$i++){
				global ${'itm'.$i},${'itmk'.$i},${'itme'.$i},${'itms'.$i},${'itmsk'.$i};
				$itm = & ${'itm'.$i};
				$itmk = & ${'itmk'.$i};
				$itme = & ${'itme'.$i};
				$itms = & ${'itms'.$i};
				$itmsk = & ${'itmsk'.$i};
				if ($itm=='黑色发卡') {$flag=true;}
				$itm = '';
				$itmk = '';
				$itme = 0;
				$itms = 0;
				$itmsk = '';
			}
		death ( 'salv', '', 0, $itm );
		//return;	
	}
		if($rename =='琉璃血'){
		$log .= "<span class=\"yellow\">呵呵，你知道的太多了。</span><br>";
		$log .= '你头晕脑胀地躺到了地上，<br>感觉整个人都被救济了。<br>';
		include_once GAME_ROOT . './include/state.func.php';
		$log .= '然后你失去了意识。<br>';
			for ($i=1;$i<=6;$i++){
				global ${'itm'.$i},${'itmk'.$i},${'itme'.$i},${'itms'.$i},${'itmsk'.$i};
				$itm = & ${'itm'.$i};
				$itmk = & ${'itmk'.$i};
				$itme = & ${'itme'.$i};
				$itms = & ${'itms'.$i};
				$itmsk = & ${'itmsk'.$i};
				if ($itm=='黑色发卡') {$flag=true;}
				$itm = '';
				$itmk = '';
				$itme = 0;
				$itms = 0;
				$itmsk = '';
			}
		death ( 'salv', '', 0, $itm );
		//return;	
	}
		if($rename =='社员专用的ID卡'){
		$log .= "<span class=\"yellow\">呵呵，你知道的太少了。</span><br>";
		$log .= '你头晕脑胀地躺到了地上，<br>感觉整个人都被救济了。<br>';
		include_once GAME_ROOT . './include/state.func.php';
		$log .= '然后你失去了意识。<br>';
			for ($i=1;$i<=6;$i++){
				global ${'itm'.$i},${'itmk'.$i},${'itme'.$i},${'itms'.$i},${'itmsk'.$i};
				$itm = & ${'itm'.$i};
				$itmk = & ${'itmk'.$i};
				$itme = & ${'itme'.$i};
				$itms = & ${'itms'.$i};
				$itmsk = & ${'itmsk'.$i};
				if ($itm=='黑色发卡') {$flag=true;}
				$itm = '';
				$itmk = '';
				$itme = 0;
				$itms = 0;
				$itmsk = '';
			}
		death ( 'salv', '', 0, $itm );
		//return;	
	}
	$mark = '';
	$rn0 = $rn;
	$rn = $mark.$rename.$mark;
//	$rnsk = str_replace('Z','x',$rnsk);
	$log .= "{$rn0}已改名为<span class=\"yellow\">$rn</span>！<br>";
	if(${'itms'.$ntitm} != $nosta){
		${'itms'.$ntitm} --;
		if(${'itms'.$ntitm} <= 0){
			$log .= "<span class=\"yellow\">{${'itm'.$ntitm}}用完了。</span><br>";
			${'itm'.$ntitm} = ${'itmk'.$ntitm} = ${'itmsk'.$ntitm} = '';
			${'itms'.$ntitm} = ${'itme'.$ntitm} = 0;		
		}
	}
	$mode = 'command';
	return;
}

# 提示纸条相关功能
function item_slip($snm,&$data)
{
	$item_slip_hint = Array
	(
		'A' => '“执行官其实都是幻影，那个红暮的身上应该有召唤幻影的玩意。”<br>“用那个东西然后打倒幻影的话能用游戏解除钥匙出去吧。”<br>',
		'B' => '“我设下的灵装被残忍地清除了啊……”<br>“不过资料没全部清除掉。<br>用那个碎片加上传奇的画笔和天然属性……”<br>“应该能重新组合出那个灵装。”<br>',
		'C' => '“小心！那个叫红暮的家伙很强！”<br>“不过她太依赖自己的枪了，有什么东西能阻挡那伤害的话……”<br>',
		'D' => '“我不知道另外那个孩子的底细。如果我是你的话，不会随便乱惹她。”<br>“但是她貌似手上拿着符文册之类的东西。”<br>“也许可以利用射程优势？！”<br>“你知道的，法师的射程都不咋样……”',
		'E' => '“生存并不能靠他人来喂给你知识，”<br>“有一套和元素有关的符卡的公式是没有出现在帮助里面的，用逻辑推理好好推理出正确的公式吧。”<br>“金木水火土在这里都能找到哦～”<br>',
		'F' => '“喂你真的是全部买下来了么……”<br>“这样的提示纸条不止这六种，其他的纸条估计被那两位撒出去了吧。”<br>“总之祝你好运。”<br>',
		'G' => '“上天保佑，”<br>“请不要在让我在模拟战中被击坠了！”<br>“空羽 上。”<br>',
		'H' => '“在研究施设里面出了大事的SCP竟然又输出了新的样本！”<br>“按照董事长的意见就把这些家伙当作人体试验吧！”<br>署名看不清楚……<br>',
		'I' => '“嗯……”<br>“制作神卡所用的各种认证都可以在商店里面买到。”<br>“其实卡片真的有那么强大的力量么？”<br>',
		'J' => '“知道么？”<br>“果酱面包果然还是甜的好，哪怕是甜的生姜也能配制出如地雷般爆炸似的美味。”<br>“祝你好运。”<br>',
		'K' => '“水符？”<br>“你当然需要水，然后水看起来是什么颜色的？”<br>“找一个颜色类似的东西合成就有了吧。”<br>',
		'L' => '“木符？”<br>“你当然需要树叶，然后说到树叶那是什么颜色？”<br>“找一个颜色类似的东西合成就有了吧。”<br>',
		'M' => '“火符？”<br>“你当然需要找把火，然后说到火那是什么颜色？”<br>“找一个颜色类似的东西合成就有了吧。”<br>',
		'N' => '“土符？”<br>“说到土那就是石头吧，然后说到石头那是什么颜色？”<br>“找一个颜色类似的东西合成就有了吧。”<br>',
		'P' => '“金符？这个的确很绕人……”<br>“说到金那就是炼金，然后这是21世纪了，炼制一个金色方块需要什么？”<br>“总之祝你好运。”<br>',
		'Q' => '“据说在另外的空间里面；”<br>“一个吸血鬼因为无聊就在她所居住的地方洒满了大雾，”<br>“真任性。”<br>',
		'R' => '“知道么，”<br>“东方幻想乡这作游戏里面EXTRA的最终攻击”<br>“被老外们称作『幻月的Rape Time』，当然对象是你。”<br>',
		'S' => '“土水符？”<br>“哈哈哈那肯定是需要土和水啦，可能还要额外的素材吧。”<br>“总之祝你好运。”<br>',
		'T' => '“我一直对虚拟现实中的某些迹象很在意……”<br>“这种未名的威压感是怎么回事？”<br>“总之祝你好运。”<br>',
		'U' => '“纸条啥的……”<br>“希望这张纸条不会成为你的遗书。”<br>“总之祝你好运。”<br>',
	);
}

//使用箭矢的功能拆在这里
function itemuse_ugb(&$pdata, $itmn){
	global $log, $mode, $nosta;
	
	$wep=&$pdata['wep']; $wepk=&$pdata['wepk']; 
	$wepe=&$pdata['wepe']; $weps=&$pdata['weps']; $wepsk=&$pdata['wepsk']; 
	
	$itm=&$pdata['itm'.$itmn]; $itmk=&$pdata['itmk'.$itmn];
	$itme=&$pdata['itme'.$itmn]; $itms=&$pdata['itms'.$itmn]; $itmsk=&$pdata['itmsk'.$itmn];
	
	//清除箭矢名
	$swapn = wep_b_clean_arrow_name($wepk);
	//清除武器上的箭属性
	$swapsk = wep_b_clean_arrow_sk($wepsk);
	//判定卸下来的箭矢数目，然后把武器改成无穷耐
	$swapnum = 0;
	if ($weps !== $nosta) {
		$swapnum = $weps;
		$weps = $nosta;
	}
	
	$wepsk_arr = get_itmsk_array($wepsk);
	$itmsk_arr = get_itmsk_array($itmsk);
	//如果是箭矢或者弓有连射属性，那么箭矢上限就是连射次数上限
	//判定连射次数按理也应该拆一个函数出来
	$arrowmax = (in_array('r',$itmsk_arr) || in_array('r',$wepsk_arr)) ? 2 + min ( floor(${$skillinfo['B']} / 200), 4 ) : 1;
	$arrownum = min($arrowmax, $itms);
	//再修改一次武器的耐久值。其实如果弄一个卸箭的功能，卸箭和上箭应该要拆成两个函数
	$weps = $arrownum;
	$itms -= $arrownum;
	
	//记录箭矢名
	$wepk .= '|'.$itm;
	//为武器增加箭属性
	if(!empty($itmsk_arr)){
		$wepsk .= '|'.implode('', $itmsk_arr).'|';
	}
	
	if(!$swapnum)	$log .= "为<span class=\"red b\">$wep</span>选用了<span class=\"red b\">$itm</span>，<span class=\"red b\">$wep</span>发射次数增加了<span class=\"yellow b\">$arrownum</span>。<br>";
	else $log .= "为<span class=\"red b\">$wep</span>换上了<span class=\"red b\">$itm</span>，<span class=\"red b\">$wep</span>发射次数增加了<span class=\"yellow b\">$arrownum</span>。<br>";
	if ($itms <= 0) {
		$log .= "<span class=\"red b\">$itm</span>用光了。<br>";
		$itm = $itmk = $itmsk = '';
		$itme = $itms = 0;
	}
	if($swapnum){
		$pdata['itm0'] = $swapn ? $swapn : '卸下的箭';$pdata['itmk0'] = 'GA';$pdata['itme0'] = 1;$pdata['itms0'] = $swapnum; $pdata['itmsk0'] = $swapsk;
		itemget();
	}
}
?>