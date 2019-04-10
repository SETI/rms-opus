String.prototype.toTitleCase = function() {
  var i, j, str, lowers, uppers;
  str = this.replace(/([^\W_]+[^\s-]*) */g, function(txt) {
    return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
  });

  // Certain minor words should be left lowercase unless
  // they are the first or last words in the string
  lowers = ['A', 'An', 'The', 'And', 'But', 'Or', 'For', 'Nor', 'As', 'At',
  'By', 'For', 'From', 'In', 'Into', 'Near', 'Of', 'On', 'Onto', 'Or', 'To', 'With'];
  for (i = 0, j = lowers.length; i < j; i++)
    str = str.replace(new RegExp('\\s' + lowers[i] + '\\s', 'g'),
      function(txt) {
        return txt.toLowerCase();
      });

  // Certain words such as initialisms or acronyms should be left uppercase
  uppers = ['Ad', 'Adc', 'Add', 'Aex', 'Af', 'Alg', 'Aprh', 'Atmo', 'Att', 'Az', 'Bacb', 'Baud', 'Bin', 'Bl', 'Cal', 'Cam', 'Ccam', 'Ccd', 'Ccsds', 'Co', 'Cmd', 'Cemis',
            'Ch1', 'Ch2', 'Ch3', 'Ch4', 'Ch5', 'Ch6', 'Ch7', 'Ch8', 'Ch9', 'Clat', 'Clk', 'Clon', 'Cmprs', 'Cpmm',
            'Convertuv', 'Convertvis', 'Convertvnir',
            'Critopnv', 'Dd', 'Dem', 'Det', 'Dll', 'Dlre', 'Dn', 'Dlnkprio', 'Dpu', 'Dsn',
            'Dx1', 'Dx2', 'Dx3', 'Dx4', 'Dx5','Dy1', 'Dy2', 'Dy3', 'Dy4', 'Dy5',
            'Edr', 'El', 'Exp', 'Et', 'Fov', 'Fpa', 'Fpu', 'Fsa', 'Fst', 'Ftp', 'Fts', 'Fw', 'Gc', 'Gop', 'Hcon', 'Hdf', 'Hk',
            'Ict', 'Id', 'Ie', 'Iea', 'If', 'Ikf', 'Img', 'Ior', 'Ir', 'Iras', 'Isis',
            'Jb', 'Jdate', 'Jpl', 'Lab', 'Lat', 'Led', 'Limb', 'Lon', 'Lro', 'Lsb', 'Lut', 'Lvl', 'Mcp', 'Md5', 'Mpen', 'Mpf', 'Mro', 'Msb', 'Msl',
            'Nssdc', 'Ntv', 'Obs', 'Oca', 'Oge', 'Omi', 'Opr',
            'Pds', 'Pi', 'Piv', 'Pls', 'Pos', 'Pre', 'Pv', 'Pws',
            'Ra', 'Rad', 'Ref', 'Refz', 'Rms', 'Roi', 'Rsc', 'Rv', 'Sam', 'Sc', 'Scalt', 'Scet', 'Sclk', 'Sclon', 'Scrad', 'Sec', 'Sef', 'Seo', 'Sfdu', 'Sol', 'Soln', 'Spice', 'Sthr', 'Subf',
            'Tb', 'Tdb', 'Tdi', 'Tec', 'Tgtb', 'Tlm', 'Tmplt', 'Tpt', 'Tv', 'Url', 'Utc', 'Vert', 'Vis', 'Vlookx', 'Vlooky', 'Vnir', 'Xo', 'X1', 'Xy',  'Yz', 'Zstack'];
  for (i = 0, j = uppers.length; i < j; i++)
    str = str.replace(new RegExp('\\b' + uppers[i] + '\\b', 'g'),
      uppers[i].toUpperCase());

  return str;
};
