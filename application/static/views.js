/////////////////////////////////
////MODELS
/////////////////////////////////

var Game = Backbone.Model.extend({});

/////////////////////////////////

var User = Backbone.Model.extend({
    urlRoot: '/user'
});

/////////////////////////////////
////VIEWS
/////////////////////////////////

var TopbarView = Backbone.View.extend({
  el: '#topbar',
  topbarTpl: _.template( $('#topbar-template').html()),

  render: function() {
    this.$el.html( this.topbarTpl( this.model.attributes ) );
    this.$("#games-list").append($('<option>', {value:'dash', id:'g'}).text('Dash'));
    for (i=1;i<this.model.attributes.games.length+1;i++){
      this.$("#games-list").append($('<option>', {value:i, id:'g'+i}).text(i));
    }
    this.$('#games-list').change(function(){
        App.game_id = $(this).children('option:selected').val();
        if (App.game_id == 'dash'){
          App.dashView.render();
        }
        else {
          if (!App.games){
            App.games = new GameCollection();
          }
          App.games.fetch({success:function(m,r,o){
            App.current_game = App.games.get(App.game_id);
            App.gameView = new GameView({'model':App.current_game}).render();
        }});
        }
    });
    return this;
  }
});

/////////////////////////////////

var DashView = Backbone.View.extend({
  el: '#display',
  dashTpl: _.template( $('#dash-template').html()),

  render: function () {
    this.$el.html( this.dashTpl( this.model.attributes ) );
    if (App.interval){
      clearInterval(App.interval);
    }
    for(i=0;i<this.model.attributes.games.length;i++){
      this.$('#game_'+this.model.attributes.games[i]).click(function(){
        if (!App.games){
          App.games = new GameCollection();
        }
        App.game_id = parseInt(this.id.slice(5));
        App.games.fetch({success:function(m,r,o){
          App.current_game = App.games.get(App.game_id);
          App.gameView = new GameView({'model':App.current_game})
          App.gameView.render();
          App.current_game.on({"change": function(){App.gameView.render();}});
        }});
      });
    }
    $.get('/user', function(data){
      App.users = data;
      console.log(App.users);
      $('#new_game').submit(function(e){
        $.post('/game', $(this).serialize(), function(data){
          if (!App.games){
            App.games = new GameCollection;
          }
          App.games.reset(data);
          App.user.fetch();
          App.dashView.render();
          App.topbarView.render();
        });
        e.preventDefault();
        return false;
      });
      App.users[0] = '';
      for (var user in App.users){
        if (user != App.user.get('id')){
          if (!$('#u'+user).length > 0){
            $("#player3").append($('<option>', {value:user, id:'u'+user}).text(App.users[user]));
            $("#player2").append($('<option>', {value:user, id:'u'+user}).text(App.users[user]));
            $("#player4").append($('<option>', {value:user, id:'u'+user}).text(App.users[user]));
          }
        }
      }
      $('select').change(function(){
        $('select option').show();
        var arr = $.map($('form select option:selected'), function(n){
          return n.value;
        });
        console.log(arr);
        $('form select option').filter(function(){
          return $.inArray($(this).val(), arr)>-1;
        })
        .hide();
      });
      $('#player3').click(function(){
        $('#player2_div').css('display', 'block');
      });
      $('#player2').click(function(){
        $('#player4_div').css('display', 'block');
      });
      $('#player4').click(function(){
        $('#submit').css('display', 'inline-block');
      });
    });
    return this;
  }
});

/////////////////////////////////

var GameView = Backbone.View.extend({
  el: '#display',
  gameboardTpl: _.template( $('#gameboard-template').html()),
  cardTpl: _.template( $('#card-template').html()),

  render: function() {
    this.$el.html( this.gameboardTpl( this.model.attributes ) );
    var turn = this.model.attributes.turn;
    var player_number = this.model.attributes.player_number;
    this.$('.cards').each(function(i, obj){
      var text = $(this).html();
      console.log(text);
      if (text.length > 1 && text.length < 4){
        console.log(text);
        var suit = text.slice(-1);
        if (suit == 'h' || suit == 'd'){
          $(this).css({'color':'red'});
        }
        $(obj).html(App.gameView.cardTpl({'card':$(this).html()}));
      }
    });
    if (this.model.attributes.message != ''){
        alert(this.model.attributes.message);
    }
    if (turn == player_number && App.current_game.get('bid') && !App.current_game.get('trump')){
      this.$('.trump').each(function(i, obj){
        $(obj).click(function(){
          $.post(App.current_game.url(), {"trump": $(this).attr('id').slice(-1)}, function(data){
            App.current_game.set(data);
          });
        });
      });
    } 
    else if (turn == player_number && App.current_game.get('bid')){
      this.$('.card').each(function(i, obj){
        $(obj).click(function(){
          $.post(App.current_game.url(), {"card": $(this).attr('id')}, function(data){
            App.current_game.set(data);
          });
        });
      });
    }
    else if (turn == player_number){
      this.$('.bid').each(function(i, obj){
        $(obj).click(function(){
          $.post(App.current_game.url(), {"bid": $(this).attr('id').slice(-1)}, function(data){
            App.current_game.set(data);
          });
        });
      });
    }
    App.wait();
    return this;
  }
});

/////////////////////////////////
////COLLECTIONS
/////////////////////////////////

var GameCollection = Backbone.Collection.extend({
  model: Game,
  url: '/game',

  parse: function(response){
    return response.models
  }
});

